# GSMG Bird-View Reassessment

> **Superseded in part by Phases 216–217:** BUT/HYE survives the
> film-versus-screenplay boundary test, and `b <-> h` with fixed `e` remains a
> bounded mirror observation. Any downstream rebus formed by selecting the
> initials of “your eyes” was circular and is excluded.

Date: 2026-07-27

## Executive conclusion

The investigation is probably not missing another broad cipher family. The
creator repeatedly describes the blocker as one recognizable microstep, and
the strongest recovered chain already reaches a coherent Architect-scene
construction:

```text
574061
-> [23,16,7]
-> BOTH / ULTIMATELY / THE
-> beginnings BUT / endings HYE
-> "both beginning and end"
-> mirrored B <-> H around fixed E
```

The most important under-audited object is the literal, case-sensitive heading
`SalPhaseIon`, considered together with the *complete* tail of the authenticated
macro clue and the exact Architect dialogue. Previous work normalized these
mostly into lowercase candidate words or treated their products as passwords.
That can miss a typography-level rebus or a narrative transition.

## What is firmly established

1. The creator's ordered macro clue is first-party page content:

   ```text
   yellowblueprimes
   matrixsumlist
   lastwordsbeforearchichoice
   yinyang
   wewontgiveawaythepassword
   itsinfrontofyoureyesbutyourenotseeingit
   verylaststepisatruegiveaway
   promised
   ```

2. The first-piece reconstruction mechanically produces prime `574061`.
   Reading its six digits as a 2x3 matrix gives total and row sums
   `[23,16,7]`.

3. Applying `[23,16,7]` to the frozen Architect speech under the uniquely
   self-checking convention selects `BOTH / ULTIMATELY / THE`. Their initial
   and final rails are `BUT / HYE`, and the source itself says the anomaly is
   revealed as **both beginning and end**.

4. The exact Architect scene also contains:

   - two doors and a choice;
   - “the salvation of Zion”;
   - the post-choice word `But`;
   - language about being blinded from a simple and obvious truth.

   These are unusually close semantic matches to the phase title and the
   creator's later “in front of your eyes” confirmation.

5. The SalPhaseIon page is a typed stream, not undifferentiated ciphertext:
   9-ary-looking data, binary-encoded instructions, decimal-transport
   instructions, literal SHA wording, Base64, and an embedded `enter`.

## Likely inherited mistake

The project has generally treated each recovered item as one of:

- a candidate passphrase;
- a cipher key;
- a selector to apply to `dbbi` or `faed`;
- material to hash and send to an AES oracle.

That framing underuses two kinds of authored information:

1. **Case and word boundaries.** The heading is specifically `SalPhaseIon`,
   visibly segmented as `Sal | Phase | Ion`.
2. **Narrative continuity.** The Architect speech simultaneously supplies
   choice, salvation, Zion, beginning/end, `But`, and blindness/obvious-truth
   language. These may be validation and routing instructions, not password
   vocabulary.

## Completed first-priority hypothesis

The heading has an exact, constrained mutation:

```text
Sal PHASE Ion
Sal VAT   Ion
SALVATION
```

The required replacement is uniquely `VAT`; it is not chosen from an open
dictionary. The authenticated tail contains the conspicuous wording:

```text
Very ... A True giveaway
```

which supplies `V-A-T` in order. This may be what “the very last step is a
true giveaway” means: the final clue gives the three letters needed to replace
the visible word `Phase`. The result, `SALVATION`, agrees with both:

- the creator's statement that breaking SalPhaseIon should give the feeling
  of the phase's name; and
- the Architect's exact phrase “the salvation of Zion.”

This is a **plausible rebus, not yet a solved transition**. Selecting `V`, `A`,
and `T` from the sentence still needs a disciplined rule; the observation must
not be promoted merely because the output is thematic. It also does not follow
that `salvation` is a literal AES password.

**Phase 96 audit result:** the archived title, creator-authored binary clue,
and five Architect-scene phrases all verify exactly. Inside the declared
four-reading family, the self-referential
`Very + A True Giveaway -> VATG`, then “give away” `G` reading is the only one
that produces the independently fixed replacement `VAT`. A focused check of
five resulting candidates generated 117 unique raw/SHA-256/double-SHA-256 and
newline keystrings and tested all four tracked/quarantined blobs across CBC,
ECB, CFB/OFB/CTR, and AES Key Wrap: zero hits. The rebus therefore remains a
strong recognition/transition hypothesis, but is closed as a direct password
under current oracle coverage.

**Phase 97 elemental correction and stronger convergence:** the archived
`SalPhaseIon` heading itself does *not* have a complete periodic-element parse;
the community's January 2026 parse silently inserted an extra `S`. The
creator's exact prose variant `salphation` does:

```text
SALPHATION = S Al P H At I O N
SALVATION  = S Al V   At I O N
```

Both parses are unique. Replacing `PH` by `V` gives:

```text
V             = 23
P + H         = 15 + 1 = 16
V - (P + H)   = 7
```

This reproduces the independently reconstructed `matrixsumlist`
`[23,16,7]` exactly and in order. The element counts also match the adjacent
page geometry: seven `SALVATION` elements times `Al=13` gives DBBI's 91 raw
symbols, while eight `SALPHATION` elements times 13 gives the 104 bits of
binary `matrixsumlist`. The atomic route therefore supplies a substantially
more constrained, mechanically selected `SALVATION` transition than the VAT rebus
alone. It still does not make `SALVATION` a direct blob password; Phase 96's
full focused oracle result remains negative.

**Phase 98 base-rate correction:** the generic atomic-number match is not
independent corroboration. Across all 1,312 distinct alphabetic word types in
the creator export, 313 fully parse into element symbols and 107/313 (34.2%)
contain some contiguous elemental span summing to 16. In the 8--12-character
band around `salphation`, the rate rises to 18/29 (62.1%). The exact
consecutive token pair `P,H` is narrower: 6/313 (1.92%) overall and 1/29
(3.45%) in the local length band. Only `salphation` becomes the fixed target
`salvation` when that exact `PH` substring is replaced by `V`. Retain this
lexical convergence as suggestive, but treat `[23,16,7]` as a
post-recognition checksum rather than proof of the intended operation.

**Phase 99 sensitivity check:** atomic numbers are the only one of five
pre-declared common value schemes (atomic, A1Z26, uppercase ASCII, English
Scrabble, and phone keypad) that maps the fixed `PH -> V` split to
`[23,16,7]`. However, applying the operation to other creator words is a
degenerate control: all six exact elemental `P,H` words necessarily produce
the same arithmetic once `PH -> V` and the periodic table are fixed. Only
`salphation` becomes the independently fixed target `salvation`. This supports
lexical specificity, not independent numeric confirmation, and does not
remove the absence of creator-authored chemistry motivation.

The title/rebus route has therefore reached its evidence ceiling. It is a
plausible recognition transition, closed as a direct password, and currently
has no authenticated binding into the textarea program.

## Completed bounded falsification audit

The deterministic audit completed the following scope:

1. Freeze the exact case-sensitive heading from archived HTML.
2. Freeze the exact macro-clue bytes and tokenization.
3. Derive the replacement target `VAT` only by string difference between
   `SALPHASEION` and `SALVATION`; do not search for arbitrary outputs.
4. Enumerate a declared small family of natural initial/terminal-letter
   readings of the final clause and report how many yield `VAT`.
5. Verify the exact “salvation of Zion,” “both beginning and end,” `choice`,
   post-choice `But`, and blindness wording in the frozen screenplay source.
6. Determine whether the resulting rule supplies:
   - a recognition checksum only;
   - a replacement instruction;
   - a choice between the `BUT` and `HYE` rails; or
   - a typed operand for the page's explicit SHA command.
7. Only if one interpretation is uniquely selected should its raw, SHA-256,
   double-SHA-256, and newline forms be checked against the already-validated
   oracles.

## Current first-priority structural audit

Treat the SalPhaseIon textarea as a left-to-right typed program and determine
operand scope before applying transforms:

```text
DBBI
-> binary("matrixsumlist")
-> FAED
-> decimal("lastwordsbeforearchichoice")
-> decimal("thispassword")
-> "sha256 our first hint is your last command"
-> SALPH blob halves separated by binary("enter")
-> raw "shabefanstoo"
```

`matrix_instruction_sweep.py` tested many matrix outputs and compositions, but
it did not prove a grammar for which field each instruction consumes. A new
audit should enumerate only syntactically natural prefix/postfix bindings and
reject interpretations that leave fields unused or require changing direction
without an explicit marker.

**Phase 101 operand-binding result:** the raw page makes fewer bindings unique
than prior prose implied. `matrixsumlist` lies exactly between DBBI and FAED,
so local order alone permits postfix-to-DBBI, prefix-to-FAED, or infix
DBBI/FAED readings. The `lastwordsbeforearchichoice` / `thispassword` pair can
describe a password for FAED, mark FAED's answer as a password, or supply the
following SALPH blob. The SHA clause can consume its explicit
`our first hint` / `your last command` words, the preceding password result,
or a preceding phase answer.

`tools/gsmg/salphaseion_operand_binding_audit.py` enumerates that closed
`3 x 3 x 3 x 2` family. The final axis is the literal suffix:

```text
shabefanstoo
sha256 + anstoo
```

Only `shabef -> sha256` is mechanical. Expanding `anstoo` to `answer too` is a
community interpretation, not decoded page text or creator confirmation.
There are 54 declared models; 27 become structurally total only under that
expansion, and **zero** are strictly supported without an unresolved or added
assumption. `SALVATION`, `VAT`, and `SalPhaseIon` are absent from the decoded
textarea instructions, so the rebus cannot be inserted as an operand on local
syntax alone.

The typed-program path is therefore not solved, but its blocker is now narrow:
recover first-party evidence for the meaning of `anstoo` and for whether the
explicit SHA operand aliases or overrides `thispassword`. Do not choose one of
the 54 models by AES outcome.

**Phase 238 house-style result:** the other authenticated slots do not supply
a missing directional convention. Six declared rules—uniform prefix,
uniform postfix, between-means-join, transport-fixes-role, nearest-neighbor
operand, and complete SHA bracketing—each has an internal counterexample.
`enter` is the only locally fixed operator because it independently rejoins
two equal 64-character halves into the authenticated SALPH blob; its success
does not generalize from position or binary transport alone. With Model B as
the current external macro default, the 54-model Phase-101 family can be
conditionally projected to 18 residual password/SHA/tail models, but this is
not creator-authenticated and still yields zero strict model. Full report:
[doc/GSMG_PAGE_SYNTAX_HOUSE_STYLE_AUDIT.md](GSMG_PAGE_SYNTAX_HOUSE_STYLE_AUDIT.md).

**Phase 102 (complete): `anstoo`/SHA-operand provenance recovered -- genuinely
unresolved, not a coverage gap.** `tools/gsmg/anstoo_provenance_audit.py`
found the creator never uses `anstoo` anywhere in the complete export and
declined the one direct request to hint at it (message `20224`, a bare
zipper-mouth reply to message `20222`); the community follow-up asking who
`our` refers to (`20226`) was never answered. All 93 community mentions of
`anstoo` are speculative; the one structurally concrete claim (a 21-row
split with `anstoo` as row 21) was challenged for its exact rule by another
community member and its own author backed it off rather than supply one.
One real structural fact was confirmed independently (not just quoted): the
six known instruction fragments concatenate to exactly 103 characters. Its
further "ends at FEFEFE" claim has no specified grid rule and is not
currently testable. No new operand-scope lever survives this audit.

**Phase 103 (complete): `SALVATION` functional-role audit.**
`tools/gsmg/salphaseion_salvation_role_audit.py` tested whether the
recognized state `SALVATION` (not as literal page text, already ruled out
above, but as an abstract role) could function as a replacement/password, a
SHA operand, a `BUT`/`HYE` rail selector, or a post-decryption checksum.
Two close negative without any new sweep: replacement/password and SHA
operand both reduce to Phase 96's already-completed 0-hit result (the SHA
operand targets the identical SALPH ciphertext). Rail selector is only a
bounded negative for literal presence/subsequence/anagram rules:
`SALVATION` shares no letters with `HYE`, only `T` with `BUT`; this does not
exclude an independently specified numeric or semantic selector. Checksum --
the decrypted SALPH plaintext
should *read like* salvation, matching message `6497`'s "breaking salphation
should be giving the feeling of the phase's name" -- is left honestly open:
it is currently unfalsifiable, since confirming it needs the correct SALPH
password already in hand. This is not a new lead to chase; it is a property
that could only be noticed after an unrelated password is found some other
way.

## Dual-channel audit (complete)

Do not assume every dual artifact must collapse immediately into one string.
Inventory the authored pairs:

- yellow / blue complementary values;
- two matrix rows;
- total `23` split as `16 + 7`;
- beginnings / endings (`BUT / HYE`);
- two 64-character SALPH Base64 halves around `enter`;
- “half and better half”;
- SalPhaseIon / Cosmic Duality textareas.

The goal is not to combine blobs arbitrarily. It is to test whether one
consistent left/right or beginning/end assignment survives the entire chain.
If assignments must be swapped independently at each step, the model fails.

**Phase 104 result: a real dependency chain exists, but it is not a conserved
dual channel.** `tools/gsmg/dual_channel_consistency_audit.py` re-derived
all seven declared pairs. Yellow-one produces prime `574061`; that produces
the two matrix rows and `23/16/7`; those positions select
`BOTH`/`ULTIMATELY`/`THE`; their edges produce `BUT`/`HYE`. But the
blue-one rose pole has no established consumer and both rails use all three
selected positions, so yellow/blue or row-1/row-2 polarity is not preserved.

A separate established link also holds: `BUT`/`HYE` filtered to `a`-`i`
symbols gives `b`/`he`;
`mirror9('b') == 'h'` with `e` fixed (Phase 34). `b` is `dbbi`'s real escape
pair; `h` gives `faed`'s mirror-hypothesis pair (`{h,e}`, not `faed`'s own
best-fit `{g,i}`).

"Half and better half" is not a settled pair at all: Phase 78 (currently
operational in the binary-key-material sweep machinery) reads it as two
32-byte keys inside one 80-byte blob, while a separate community theory
bridging it to `SalPhaseIon`/`Cosmic Duality` specifically already failed a
direct oracle test (Phase 54). Treating that failed reading as the "real"
one just to complete the chain would repeat the exact apophenia pattern this
project has already caught and corrected (Phase 13's "matrixsumlist
triangle", the Cross-Phase Review's "yang" debunk).

No further chemistry, numerology, or password sweep follows from this
result.

## Explicitly deprioritized

- More generic checkerboard, substitution, digraphic, adjacent-difference, or
  prime-zeroing sweeps without a new selector.
- Treating literal `yang`, `FE`, `ED`, `89`, `97`, `163`, or `574061` as
  passwords merely because they are present.
- More anagram search over the 31 selected characters.
- `help.gsmg.io` as a puzzle dependency: the archived puzzle HTML contains no
  such link; the subdomain appears in the mirrored application's ordinary help
  configuration, not in the SalPhaseIon/Cosmic page.
- Assuming the two historical routes must cryptographically converge merely
  because a community diagram drew that arrow.

## Priority order

1. ~~Run a calibrated blind monoalphabetic FAED recovery under `{g,i}`.~~
   **DONE (Phase 113), closed negative.** Real FAED (800 restarts/4000
   iters, canonical `(g,i,top_first)` variant): best score -2419.47.
   Pre-registered staged token-preserving null (100 trials, same optimizer
   seed/budget): 3/100 exceedances, empirical p=0.0396 -- fails the
   project's p<0.005 bar (softer than Phase 43's `(h,e)` result, which sat
   at the null median, but still not significant). No AES escalation ever
   ran. `{g,i}` remains the best-supported escape pair by code-IC/frequency
   fit, but does not provide project-threshold evidence of English via
   ciphertext-only monoalphabetic recovery at this evidence level. See
   `tools/gsmg/FINDINGS.md` Phase 113
   for the full staged-design/hardening writeup, including a provenance
   caveat (the completed run predates a review-fix pass to the escalation
   pipeline's fingerprinting -- moot here since the gate failed and
   escalation never executed).
2. ~~Audit the recovered Phase-4 comparison artifact (Telegram message
   `8088`) under one fixed custom-Architect-text versus screenplay
   alignment.~~ **DONE (Phase 118), closed negative.** The deterministic
   word-LCS comparison isolates 164 custom-only words, but all four
   prime-indexed letter streams are non-language. The lone `list` marker has
   family-wise empirical `p=0.0266` under 5,000 character-multiset shuffles
   and fails the project's `p<0.005` bar. Phase 117 separately shows the Neo
   passport clue most plausibly reinforces `DD MON YY` date recognition
   (`11 SEP 01` / `01 APR 21`) and closes those exact inscriptions as direct
   keys. Do not expand alignments, date formats, or prime masks without a new
   selector.
3. Recover physical book pages 57-58 as the remaining physical-evidence gap.
4. Reopen one narrowly changed model: FAED `{g,i}` under the VIC-style
   chain-addition layer. The historical large run predates the corrected
   oracle and per-target escape configuration; Phase 112 later made `{g,i}`
   the independently best-supported FAED pair, while Phase 113 closed only a
   single-layer monoalphabetic model. Harden the driver with fingerprinted,
   exact checkpoint/resume before running. See
   [doc/GSMG_PHASE_REOPENING_REASSESSMENT.md](GSMG_PHASE_REOPENING_REASSESSMENT.md).
5. Keep `-nopad` Tier 2 and the large autokey continuation as background
   coverage only; the former is bounded and cheap, while the latter remains
   weakly motivated.

`anstoo`/SHA-operand provenance (Phase 102) and the dual-channel consistency
audit (Phase 104) are complete. Phase 103 closes two exact roles, bounds one,
and leaves checksum explicitly untestable. See those phases, the Phase-112
IC correction, and the Phase-113 `{g,i}` recovery closure in
`tools/gsmg/FINDINGS.md`.

No further chemistry/numerology or password sweep is justified without new
creator-authored periodic-table evidence or a genuinely new, independently
specified rule -- not another guess at an already-tested premise. Every
concretely-pursuable angle from local page structure, the title/macro-clue
rebus, the `anstoo` literal, and cross-artifact duality has now been
audited, including the `{g,i}` ciphertext-only recovery (Phase 113, closed
negative). What remains is primarily evidence recovery (book pp. 57-58;
Phase 119 confirms no `barrystyle` interior-page attachment exists in the
currently retained complete Telegram export), plus one narrowly justified
computational reopening: FAED `{g,i}` under the VIC-style chain-addition
layer.

The central question is now not a cryptanalytic one at all, but an
evidence-availability one:

> Is there any remaining primary source -- physical or archival -- not yet
> examined, or has this investigation genuinely exhausted every artifact
> currently available to it?
