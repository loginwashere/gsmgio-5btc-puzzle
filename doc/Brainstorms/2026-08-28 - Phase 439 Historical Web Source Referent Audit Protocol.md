---
type: preregistration
phase: 439
date: 2026-08-28
status: frozen-before-execution
oracle: forbidden
gpu: forbidden
---

# Phase 439 — Historical Web-Source Referent Audit Protocol

## Question

Does `RETURN TO THE SOURCE CODES` identify creator-served historical page
source as a distinct referent omitted by Phase 437, and does any such object
become sufficiently specified for a later prime extraction?

This audit distinguishes original web responses from this project's later
source repository. It inventories and gates objects; it does not decode or try
passwords.

## Evidence fixed before execution

- Original lowercase `/puzzle` served a PNG directly, not an HTML document.
- The post-2026-restoration `Puzzle.html` is not attributable to the original
  creator and postdates the Architect instruction.
- The SalPhaseIon/Cosmic HTML is downstream of the instruction and therefore
  cannot satisfy a literal backward `RETURN` without additional evidence.
- The two chronologically prior real HTML pages are `theseedisplanted` and the
  long `choiceisanillusion...iwroteitmyself` Phase-2/3 page.
- Their raw local Wayback-mirror copies have SHA-256 values
  `5356c887...63136` and `7237ce18...fbf9b`, respectively.
- Both contain source-only HTML comments ending `Good luck little bunny hunter
  ;)`; the visible page does not display those comments.
- Both raw captures also contain request/deployment material: CSRF tokens and
  Cloudflare beacon markup. The repository's committed readable copies are
  normalized reconstructions, not byte-identical raw responses.
- Creator support-group message 28703 identifies the changing web mechanism as
  anti-bruteforce behavior; message 28794 says scanning GSMG generally “Won't
  work”; message 28812 points to `/puzzle` and says all needed information is
  there.
- Preliminary solver-group inspection found no creator-authored exact-comment,
  `html source`, or `source code` hit and no direct creator reply to those hits.

## Frozen objects

The audit must classify exactly these families:

1. raw `theseedisplanted` HTML;
2. raw `choice...iwroteitmyself` HTML;
3. the ordered pair of those full HTML responses;
4. the ordered pair of their source-only HTML comments;
5. their CSRF token values;
6. their HTML tags/attributes and Cloudflare script material;
7. their textarea ciphertext payloads;
8. original lowercase `/puzzle`;
9. restored `Puzzle.html`;
10. SalPhaseIon/Cosmic HTML;
11. general GSMG JavaScript/site assets.

No new family may be introduced after execution begins.

## Measurements

- raw and normalized-copy sizes/hashes;
- HTML comments, forms, CSRF metadata/inputs, scripts, and textareas per prior page;
- exact common suffix and page-specific comment prefixes;
- whether script elements are puzzle-authored or external deployment analytics;
- creator constraints at support IDs 28703, 28794, and 28812;
- solver-export counts and creator reply edges for the fixed terms
  `nice to see you around`, `you made it to the next step`,
  `good luck little bunny hunter`, `html source`, and `source code`;
- prior coverage and failed eligibility gates for every frozen object.

## Eligibility gates

An executable referent must pass all of:

1. `creator_puzzle_artifact` — not later repository/restoration/deployment noise;
2. `chronologically_returnable` — available no later than the instruction's stage;
3. `stable_representation` — exact bytes or normalization fixed by the puzzle;
4. `locally_selected` — the instruction selects this object over competing sources;
5. `operator_fixed` — `PRIME BASICS` fixes the operation sufficiently;
6. `unit_boundary_fixed` — index base, byte/character/token unit, direction,
   retained rail, concatenation order, and extent are fixed;
7. `consumer_fixed` — serialization and downstream consumer are fixed;
8. `genuinely_uncovered` — the exact family is absent from registered coverage.

Source-only comments may be recorded as a genuine omitted referent even if they
fail execution gates. CSRF/session values must fail `stable_representation` if
the creator evidence identifies them as changing anti-bruteforce state.

## Allowed dispositions

- `eligible_source_referent_requires_execution_preregistration`;
- `new_source_referent_registered_but_ineligible`;
- `historical_web_source_fully_subsumed`;
- `no_authenticated_historical_source_object`.

## Stop conditions

No prime indexing, comment recombination, candidate password generation, oracle
call, network request, Docker action, or GPU interaction is allowed. An eligible
object would require a separate frozen execution protocol.
