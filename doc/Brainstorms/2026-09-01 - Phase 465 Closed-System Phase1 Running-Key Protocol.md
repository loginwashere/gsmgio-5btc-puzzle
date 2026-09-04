---
type: preregistration
phase: 465
date: 2026-09-01
status: frozen-before-execution
---

# Phase 465 — Closed-System Phase-1 Running-Key Protocol

## Hypothesis

Phase 461's `THEFLOWER` checkpoint may be a routing instruction back to the
authenticated Stage-1 credential
`theflowerblossomsthroughwhatseemstobeaconcretesurface`. Under the creator's
“No need. You have all the info” constraint, the credential may function as a
running key over an unresolved `a-i` stream rather than as another direct AES
password.

This is newly motivated by `THEFLOWER`; it is not a generic keyword sweep.
The full credential has been tested directly against locks, and unused song
lines have been tested as checkerboard keywords, but the full authenticated
credential has not been applied through the existing Phase-310/320 modular
running-key mechanisms over DBBI/FAED.

## Frozen inputs

- exact DBBI and FAED strings from `tools/gsmg/data.py`;
- exact 53-letter Stage-1 credential from
  `tools/gsmg/first_hint_hash_audit.py`;
- the 44-letter continuation strictly after the recovered prefix
  `theflower`;
- target-specific escape pairs already registered by prior work:
  DBBI `(b,e)/(e,b)`; FAED `(g,i)/(i,g)/(h,e)/(e,h)`;
- the two established code-slot topologies, `top_first` and
  `escapes_first`.

File hashes and this family are pinned in
`tools/gsmg/phase465_phase1_running_key_manifest.json`.

## Frozen transforms

Two inherited insertion points only:

1. **raw-base9:** map credential letters with Phase 320's `A=0 ... Z=25
   (mod 9)` convention, add or subtract the repeated key from raw `a-i`
   symbols, then segment;
2. **code-slot25:** segment first, map credential letters with Phase 310's
   25-letter `J -> I` convention, then add or subtract the repeated key modulo
   25.

For each key scope, test every cyclic key offset. Offset zero is the
pre-registered prediction because the authenticated credential begins with
the recovered `THEFLOWER`. The nonzero cyclic offsets are matched internal
controls with identical bytes, length, and letter frequencies.

No reversal, word reordering, alternate alphabet, arbitrary offset into the
ciphertext, new escape pair, or password normalization is allowed.

## Staged detector

Tier 1 is deterministic and cheap. For every target, insertion point, sign,
key scope, and cyclic offset, retain the best target-registered
escape/topology route by proximity of its code-slot Index of Coincidence to
English (`0.0667`). Record offset zero's exact rank among all offsets.

Tier 2 is allowed only for a configuration where offset zero ranks first on
FAED. Run the inherited substitution hill-climber on offset zero and the four
best nonzero controls under exactly the same fixed budget and stable seeds.

## Promotion gates

Promotion requires all of:

1. offset zero ranks first structurally for FAED within its complete cyclic
   control family;
2. offset zero also ranks first by Tier-2 quadgram score against the four
   strongest nonzero controls;
3. the decoded output contains a clear multiword English instruction or an
   exact authenticated target not supplied to the scorer; and
4. the result survives rerunning with a second fixed hill-climb seed budget.

An IC rank alone is not a discovery. If no configuration passes all gates,
close only this precise Phase-1-running-key family.

## Prohibitions and stop rule

- no AES, password, private-key, address, route, or hash oracle;
- no dictionary expansion or language-driven key mutation;
- no `BLOSSOMS` fitting beyond the fixed authenticated continuation scope;
- no use of an attractive partial decode to change the family.

Stop after the frozen family and controls. A negative result redirects the
closed-system program toward a global instruction/operand constraint model,
not another running-key variant.
