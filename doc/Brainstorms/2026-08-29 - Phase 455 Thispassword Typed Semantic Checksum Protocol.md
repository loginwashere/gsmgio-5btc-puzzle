---
type: hypothesis
phase: 455
date: 2026-08-29
status: frozen
topics:
  - thispassword
  - typed-constraints
  - topology
  - non-oracle
---

# Phase 455 — Thispassword Typed Semantic Checksum Protocol

> [!caution] Frozen before execution
> The roles, evidence facts, constraint axes, state vocabulary, and verdict
> mapping below are fixed before the checker is run. This is a compatibility
> audit, not a weighted score or password search.

## Question

Does treating authenticated nearby words as strict type constraints eliminate
any of Phase 101's three unresolved `thispassword` roles under a fourth test
that is distinct from Phases 373/376/377?

This implements item 9 in
[Post-Phase-452 Scientific Experiment Portfolio](2026-08-29%20-%20Post-Phase-452%20Scientific%20Experiment%20Portfolio.md).

## Frozen roles

| ID | Existing role | Typed claim |
|---|---|---|
| R1 | `password_for_faed` | a password-like input is consumed by a transform of FAED and yields decoded FAED content |
| R2 | `faed_answer_is_password` | `lastwordsbeforearchichoice` transforms FAED; its result is labeled a password, with its eventual consumer unbound |
| R3 | `password_for_salph_blob` | an Architect/FAED-adjacent result is a passphrase-like input consumed by the SALPH OpenSSL envelope |

These names and their exclusivity are inherited unchanged from Phase 101. No
fourth role may be introduced after inspecting the result.

## Frozen authenticated facts

1. Literal order is
   `FAED -> lastwordsbeforearchichoice -> thispassword -> sha256... -> SALPH-prefix -> enter -> SALPH-suffix`.
2. No explicit attachment marker selects backward labeling, backward reach to
   FAED, or forward reach to SALPH (Phase 377).
3. `enter` is the established binary instruction between two 64-character
   SALPH Base64 halves. Removing the instruction and concatenating the halves
   reconstructs a valid envelope beginning `Salted__`. It is therefore a
   formatting/reconstruction instruction, not evidence for a password-entry
   interface.
4. The SALPH bytes are an OpenSSL salted envelope, which establishes a
   passphrase-consuming object type but not which nearby result supplies it.
5. FAED is an authenticated raw digit stream without a locally authenticated
   container signature or entry interface. That absence does not prove it
   cannot take a key.
6. `thispassword` authenticates the result class `password` somewhere in
   the local program but contains no explicit target, length, cardinality, hash
   state, or serialization.
7. `sha256 our first hint is your last command` is a separate instruction
   with its own stated operand. Adjacency alone may not retype
   `thispassword` as either a raw or hashed value.
8. No authenticated source fixes the byte length or token cardinality of the
   value denoted by `thispassword`.
9. `lastwordsbeforearchichoice` is transform-like and word-producing, but
   its concrete input/output remains blocked by `G-ARCH-001`.

The solved Phase 2/3/3.2 boundaries are a positive control for the rule that
an explicit imperative plus an explicit operand may bind an operation. They do
not contain this page's postpositive attachment pattern and cannot select R1,
R2, or R3.

## Frozen axes and cell states

Each role is checked independently on exactly seven axes:

1. literal page order;
2. input/output type;
3. enterability;
4. hash state;
5. result class;
6. explicit cardinality/length;
7. object consumed.

Every cell receives exactly one state:

- `compatible`: the role can satisfy the authenticated fact without changing
  the role or contradicting a scoped instruction;
- `contradicted`: an authenticated fact or solved-boundary positive control
  makes the typed claim impossible;
- `unbound`: present evidence does not fix the field.

`compatible` is not evidential support and earns no score. `unbound` is not
a contradiction. A role survives if and only if it has zero
`contradicted` cells.

## Pre-registered role matrix

| Axis | R1 | R2 | R3 |
|---|---|---|---|
| literal page order | compatible but requires unmarked backward reach | compatible but requires unmarked backward label | compatible but requires unmarked forward reach |
| input/output type | password-like input and decoded-FAED output are unbound | FAED-derived answer typed as password is compatible; concrete transform unbound | passphrase input is compatible with SALPH envelope; source/result unbound |
| enterability | unbound; no FAED entry interface | unbound; eventual password consumer absent | compatible cryptographic input, but `enter` supplies no support |
| hash state | unbound | unbound | unbound |
| result class | decoded FAED content unbound | password class compatible with literal token | SALPH plaintext class unbound |
| explicit cardinality/length | unbound | unbound | unbound |
| object consumed | FAED is claimed but attachment unbound | no local object is claimed; eventual consumer unbound | SALPH is typed as consumable but attachment unbound |

No matrix cell is pre-registered as contradicted. Execution may change a cell
only if re-derivation of a pinned authenticated fact fails; it may not change
because one role sounds more natural.

## Verdict mapping

- `one_role_survives`: exactly one role has zero contradictions.
- `multiple_roles_survive`: exactly two roles have zero contradictions.
- `all_roles_survive`: all three roles have zero contradictions.
- `constraint_system_inconsistent`: no role survives or an authenticated fact
  is internally inconsistent with the frozen page reconstruction.

## Exclusions and stop rule

- No password generation, hashing of candidate values, decryption, language
  scoring, oracle calls, synonym expansion, or community interpretation.
- No weighted support score and no tie-break by number of `compatible` cells.
- Stop after deriving the seven-by-three matrix and its mechanical verdict.
- A tie records underdetermination; it does not license another internal
  ranking pass.

## Gap effect

Only `one_role_survives`, backed by at least one hard contradiction against
each rival, may narrow the three-role question. It still cannot supply the
winning role's operand or close `G-ARCH-001`, `G-ESC-001`, or a blob
password gap without their own closure evidence.
