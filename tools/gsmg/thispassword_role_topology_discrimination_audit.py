#!/usr/bin/env python3
"""Attempt to discriminate Phase 101's three unreconciled `thispassword`
roles by scoring dataflow topology, per the user's exact 2026-08-22
framing (the follow-up to Phase 372's retracted overclaim, tracked in
`doc/GSMG_TOPOLOGY_AUDIT.md`).

CORRECTED SAME-DAY (user review): the first version of this audit
produced a confident unique winner (`password_for_salph_blob`) that was
itself an artifact of disputed feature assignments, not independently
extracted structure. Three concrete defects were identified: (1)
`faed_answer_is_password` was scored as though it had to skip
`lastwordsbeforearchichoice` to bind directly on raw FAED, when its
natural graph is FAED -> lastwordsbeforearchichoice -> answer ->
postpositive `thispassword` label -- no skip required; (2)
`password_for_salph_blob` measured adjacency/vocabulary against
`hash_prefix`, a separate, already-scoped instruction with its own SHA
operand (Phase 121/372) -- re-conflating the two referents Phase 372
deliberately separated; (3) `precedent_match` was awarded only to the
SALPH role despite message 8446 fixing token ORDER, not a consumption
edge -- exactly the checkpoint/operand distinction Phase 369 itself
established. A fourth, more fundamental issue: the calibration boundaries
(Phase 3, Phase 3.2) validate only "is this explicitly, unambiguously
consumed at all" -- a different, easier question than the postpositive/
ambiguous attachment `thispassword` actually poses, which no solved GSMG
boundary calibrates.

This file now keeps BOTH the original (disputed, retracted)
`role_candidates_disputed()` and a `role_candidates_corrected()` that
fixes defects (1)-(3), and checks in `self_test()` that they DISAGREE on
the winner -- that disagreement is itself the evidence that the earlier
conclusion was model-dependent, not structurally forced. Combined with
`CALIBRATION_ANALOG_AVAILABLE = False` (defect 4), the verdict is
inconclusive/model-dependent and `operand_ranking_licensed` is False.
Per the user's explicit stop rule: do not invent a new "comparable"
solved boundary to force the calibration gate closed. Phase 101's three
`thispassword` roles remain unresolved.

This does NOT generate any password candidate and does NOT run any
transform, cipher, or hash comparison. It scores three already-known,
already-named candidate roles (cross-checked in self_test() against
`salphaseion_operand_binding_audit.py`'s own generated `password_role`
values, not retyped) on seven frozen dimensions, using only:

  - the byte-verified literal page segmentation
    (`page_structure_audit.segment_salphaseion`);
  - the creator-authored order fact from Phase 121
    (`binary_hint_operand_audit.py` / message 8446): the fixed high-level
    chain `yellowblueprimes -> matrixsumlist -> lastwordsbeforearchichoice
    -> yinyang`, which fixes token ORDER only, never a consumption edge,
    and never mentions `thispassword` at all -- so it is NOT used to
    differentially favor any one role (`precedent_match` is False for all
    three candidates in the corrected modeling).

Frozen scoring dimensions (equal unit weight, predeclared before scoring
Phase 101 -- see `calibration_candidates()` for where they are fixed):
    1. exact page/instruction order (forward vs. backward direction)
    2. immediate adjacency to the claimed consumer (content-token hops,
       z-separators excluded as non-content)
    3. explicit password/SHA vocabulary co-occurring with the claimed
       consumer
    4. solved-stage directionality precedent (leave-one-out across the
       other known/authenticated ordered chains)
    5. number of unsupported edges (a binding the candidate asserts with
       no local instruction licensing it -- e.g. reading backward across
       an intervening instruction, or treating an explicit instruction as
       a silent no-op)
    6. number of unresolved operand bindings (a binding the candidate
       claims exists, whose concrete value is not established -- honestly
       left open, not asserted)
    7. RULE, not a scored dimension: a recognition checkpoint (no
       consumer claimed at all) is never penalized merely for being
       unconsumed -- it is scored on dimensions 1-6 like anything else.

Ties are a predeclared valid outcome (see `classify_ranking`) -- nothing
here forces a unique winner if the scores tie.

Operand ranking (naming a specific value, e.g. G-ARCH-001, as a candidate
for whichever role eventually wins) is NOT performed here and is NOT
licensed by this audit's current state -- see `self_test()`'s own
source-guard against reintroducing Phase 372's retracted overclaim.

Usage:
    python3 tools/gsmg/thispassword_role_topology_discrimination_audit.py
    python3 tools/gsmg/thispassword_role_topology_discrimination_audit.py --self-test
"""
import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from page_structure_audit import (  # noqa: E402
    DEFAULT_HTML,
    TextareaParser,
    normalize_salphaseion,
    segment_salphaseion,
)
from page_structure_audit import audit as audit_page  # noqa: E402
from salphaseion_operand_binding_audit import (  # noqa: E402
    EXPECTED_SEGMENTS,
    candidate_models,
)


# ---------------------------------------------------------------------------
# Scoring primitive -- identical formula used for calibration and for the
# real Phase 101 role scoring. No boundary-specific or role-specific
# branching lives in this function; only the inputs differ.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TopologyCandidate:
    name: str
    forward_direction: bool
    adjacency_distance: int  # content-token hops to the claimed consumer
    vocabulary_match: bool
    precedent_match: bool
    unsupported_edges: int
    unresolved_bindings: int
    note: str = ""

    @property
    def score(self) -> int:
        return (
            int(self.forward_direction)
            + max(0, 2 - self.adjacency_distance)
            + int(self.vocabulary_match)
            + int(self.precedent_match)
            - self.unsupported_edges
            - self.unresolved_bindings
        )


def classify_ranking(candidates):
    """Rank candidates by score, descending. Reports a tie whenever more
    than one candidate shares the top score -- this is a real, exercised
    code path (see self_test()'s synthetic-tie check), not a hypothetical
    the ranking logic silently forecloses."""
    ordered = sorted(candidates, key=lambda c: c.score, reverse=True)
    top_score = ordered[0].score
    winners = tuple(c.name for c in ordered if c.score == top_score)
    return {
        "ordered": tuple((c.name, c.score) for c in ordered),
        "winners": winners,
        "unique_winner": winners[0] if len(winners) == 1 else None,
        "tie": len(winners) > 1,
    }


# ---------------------------------------------------------------------------
# Calibration: the same rule applied to the two solved multi-component
# boundaries (Phase 2 is excluded, matching solved_boundary_rule_audit.py's
# own reasoning -- a single component has no order/adjacency question to
# get right, so it cannot discriminate topologies at all).
# ---------------------------------------------------------------------------

def calibration_candidates():
    """Both Phase 3 and Phase 3.2 carry an explicit, textual, forward
    consumption instruction ("Concatenate them all and perform SHA256";
    "just add giveit in front of the answer") naming their components
    directly -- this is read from the page text itself, not from any hash
    match, so using it as a scoring input is not circular. Leave-one-out
    precedent: each boundary's `precedent_match` is grounded in the OTHER
    boundary's structure, never its own."""
    boundaries = {}
    for name, other_name in (("phase3", "phase3_2"), ("phase3_2", "phase3")):
        # Both known boundaries independently show forward, ordered,
        # vocabulary-anchored, fully-consumed structure -- so leave-one-out
        # precedent is True for the linear reading in both directions.
        del other_name  # documented, not branched on: both boundaries agree
        boundaries[name] = (
            TopologyCandidate(
                name="linear_consumed",
                forward_direction=True,
                adjacency_distance=0,  # instruction directly names components
                vocabulary_match=True,  # explicit "perform SHA256" / "giveit"
                precedent_match=True,
                unsupported_edges=0,
                unresolved_bindings=0,
                note="components consumed forward, in the order the page "
                     "states them, into the page's own explicit operation",
            ),
            TopologyCandidate(
                name="order_invariant_consumed",
                forward_direction=True,
                adjacency_distance=0,
                vocabulary_match=True,
                precedent_match=False,  # neither boundary's text says order is free
                unsupported_edges=1,  # assumes the stated order is decorative
                unresolved_bindings=0,
                note="same consumption, but assumes the page's stated "
                     "component order does not matter -- not licensed by "
                     "either boundary's text",
            ),
            TopologyCandidate(
                name="unconsumed_checkpoint",
                forward_direction=False,
                adjacency_distance=5,  # no claimed binding to any consumer
                vocabulary_match=False,  # ignores the explicit instruction text
                precedent_match=False,
                unsupported_edges=1,  # ignores an explicit consumption instruction
                unresolved_bindings=0,
                note="claims the components are never actually consumed -- "
                     "directly contradicted by the page's own explicit "
                     "'perform SHA256' / prefix instruction",
            ),
        )
    return boundaries


def run_calibration():
    boundaries = calibration_candidates()
    results = {name: classify_ranking(cands) for name, cands in boundaries.items()}
    gate_passed = all(
        r["unique_winner"] == "linear_consumed" for r in results.values()
    )
    return {"boundaries": results, "gate_passed": gate_passed}


# ---------------------------------------------------------------------------
# Phase 101's three `thispassword` (password_role) candidates, scored with
# the identical rule and identical unit weights.
# ---------------------------------------------------------------------------

CONTENT_SEGMENT_NAMES = tuple(
    n for n in EXPECTED_SEGMENTS if not n.startswith("z_separator")
)


def content_distance(a, b):
    """Hops between two segment names in the content-only (z-separators
    excluded) page order -- excluding separators because they are pure
    delimiters with no instruction/data content of their own, per
    page_structure_audit's own segmentation."""
    return abs(CONTENT_SEGMENT_NAMES.index(a) - CONTENT_SEGMENT_NAMES.index(b))


CALIBRATION_ANALOG_AVAILABLE = False
# Corrected same-day (user review): Phase 3 / Phase 3.2 calibrate only
# "is this component explicitly, unambiguously consumed at all" (their page
# text says "Concatenate them all and perform SHA256" / "just add giveit in
# front of the answer" -- no attachment ambiguity exists there at all). The
# actual Phase 101 question is different in kind: does a short trailing
# instruction-like token (`thispassword`) attach BACKWARD as a postpositive
# label on the immediately preceding operation's result, or FORWARD onto a
# following object? No solved GSMG boundary in this project exhibits that
# specific postpositive/ambiguous-attachment structure, so the calibration
# gate below validates the scoring ARITHMETIC, not its license to attach a
# pronoun-like instruction in this specific way. Per the user's explicit
# stop rule: do not invent a new "comparable" boundary to force a gate
# closed -- leave this False and keep Phase 101 unresolved until a genuine
# analog is found.


def role_candidates_disputed():
    """Phase 373's ORIGINAL modeling, kept verbatim (not fixed) so its
    disagreement with `role_candidates_corrected()` below is a live,
    checked fact rather than an assertion. Retracted same-day -- do not
    use for anything but the model-dependence regression in self_test().

    Known defects (user review, 2026-08-22): (1) `faed_answer_is_password`
    is scored as though it must skip `lastwordsbeforearchichoice` to bind
    directly to raw FAED, when its natural graph is FAED ->
    lastwordsbeforearchichoice -> answer -> postpositive `thispassword`
    label -- no skip required. (2) `password_for_salph_blob` measures
    adjacency/vocabulary against `hash_prefix`, a separate, already-scoped
    instruction with its own SHA operand (Phase 121/372) -- re-conflating
    the two referents Phase 372 deliberately separated. (3)
    `precedent_match` was awarded only to the SALPH role despite message
    8446 fixing token ORDER, not consumption edges (Phase 369's own
    checkpoint/operand distinction)."""
    dist_to_faed = content_distance("decimal_instruction_2", "faed")
    dist_to_hash_prefix = content_distance("decimal_instruction_2", "hash_prefix")

    return (
        TopologyCandidate(
            name="password_for_faed",
            forward_direction=False,
            adjacency_distance=dist_to_faed,
            vocabulary_match=False,
            precedent_match=False,
            unsupported_edges=1,
            unresolved_bindings=1,
            note="[disputed] unlocks raw FAED directly",
        ),
        TopologyCandidate(
            name="faed_answer_is_password",
            forward_direction=False,
            adjacency_distance=dist_to_faed,  # disputed: measures to raw FAED
            vocabulary_match=False,
            precedent_match=False,
            unsupported_edges=1,  # disputed: treats lastwordsbeforearchichoice as a no-op
            unresolved_bindings=0,
            note="[disputed] retroactive label on FAED, skipping lastwordsbeforearchichoice",
        ),
        TopologyCandidate(
            name="password_for_salph_blob",
            forward_direction=True,
            adjacency_distance=dist_to_hash_prefix,  # disputed: measures to hash_prefix, not the blob
            vocabulary_match=True,  # disputed: conflates thispassword with hash_prefix's own SHA operand
            precedent_match=True,  # disputed: message 8446 fixes order, not this consumption edge
            unsupported_edges=0,
            unresolved_bindings=1,
            note="[disputed] announces the following SALPH blob's password requirement",
        ),
    )


def role_candidates_corrected():
    """Corrected same-day per user review. Each role's claimed TARGET is
    now the object the role's own name actually names, not a proxy:

      - password_for_faed: raw FAED itself (unchanged -- this is the one
        role whose name explicitly claims to reach past
        lastwordsbeforearchichoice to bind on FAED's raw bytes).
      - faed_answer_is_password: `lastwordsbeforearchichoice`'s own OUTPUT
        (the immediately preceding instruction's result) -- `thispassword`
        as a postpositive label on it. No skip, no no-op assumption: this
        is the plain adjacent-backward reading.
      - password_for_salph_blob: the actual SALPH ciphertext segment
        (`salphaseion_aes_prefix`), not `hash_prefix`. `hash_prefix` is a
        separate, already-scoped instruction with its own SHA operand
        (Phase 121/372) -- reaching the blob past it is itself an
        unsupported edge, and the blob carries no vocabulary of its own
        (it is raw base64 ciphertext), so vocabulary_match is False here.

    `precedent_match` is False for all three: message 8446 fixes token
    ORDER only (`matrixsumlist -> lastwordsbeforearchichoice -> yinyang`),
    never a consumption edge, and never mentions `thispassword` at all --
    using it to differentially favor one role would repeat exactly the
    checkpoint/operand conflation Phase 369 flagged."""
    dist_to_faed = content_distance("decimal_instruction_2", "faed")
    dist_to_lastwords_output = content_distance("decimal_instruction_2", "decimal_instruction_1")
    dist_to_salph_blob = content_distance("decimal_instruction_2", "salphaseion_aes_prefix")

    return (
        TopologyCandidate(
            name="password_for_faed",
            forward_direction=False,
            adjacency_distance=dist_to_faed,
            vocabulary_match=False,
            precedent_match=False,
            unsupported_edges=1,  # reaches past lastwordsbeforearchichoice to bind on raw FAED
            unresolved_bindings=1,
            note="thispassword's operand is claimed to unlock raw FAED itself",
        ),
        TopologyCandidate(
            name="faed_answer_is_password",
            forward_direction=False,  # still a backward-pointing label
            adjacency_distance=dist_to_lastwords_output,  # immediately adjacent, not 2 hops
            vocabulary_match=True,  # "password" sits directly touching the labeled result
            precedent_match=False,
            unsupported_edges=0,  # no skip: labels the immediately preceding result directly
            unresolved_bindings=0,  # a checkpoint label with no further claimed consumer
            note="thispassword is a postpositive label directly on "
                 "lastwordsbeforearchichoice's own output -- no skip required",
        ),
        TopologyCandidate(
            name="password_for_salph_blob",
            forward_direction=True,
            adjacency_distance=dist_to_salph_blob,  # to the actual blob, not hash_prefix
            vocabulary_match=False,  # the blob itself is raw ciphertext, no vocabulary
            precedent_match=False,
            unsupported_edges=1,  # reaches past hash_prefix's own separately-scoped SHA operand
            unresolved_bindings=1,
            note="thispassword is claimed to announce the SALPH blob's "
                 "password requirement, past the intervening hash_prefix instruction",
        ),
    )


def run_role_discrimination():
    disputed_ranking = classify_ranking(role_candidates_disputed())
    corrected_ranking = classify_ranking(role_candidates_corrected())
    models_agree = disputed_ranking["unique_winner"] == corrected_ranking["unique_winner"]
    # Licensing requires BOTH a calibration analog for this specific kind
    # of attachment ambiguity (there is none) AND agreement between
    # defensible modelings (there is none either -- they disagree). Either
    # gap alone would be sufficient to withhold licensing.
    operand_ranking_licensed = CALIBRATION_ANALOG_AVAILABLE and models_agree
    return {
        "disputed_ranking": disputed_ranking,
        "corrected_ranking": corrected_ranking,
        "models_agree": models_agree,
        "operand_ranking_licensed": operand_ranking_licensed,
        "operand_ranking_performed": False,
        "note": (
            "Inconclusive/model-dependent: the disputed and corrected "
            "role modelings disagree on the winner "
            f"({disputed_ranking['unique_winner']!r} vs. "
            f"{corrected_ranking['unique_winner']!r}), and no solved GSMG "
            "boundary calibrates the specific postpositive/ambiguous-"
            "attachment question thispassword poses. Phase 101's three "
            "roles remain unresolved; operand ranking is not licensed."
        ),
    }


# ---------------------------------------------------------------------------
# Full audit
# ---------------------------------------------------------------------------

def literal_segments(html_path=DEFAULT_HTML):
    parser = TextareaParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    salphaseion_raw = parser.textareas[0]
    stream = normalize_salphaseion(salphaseion_raw)
    return segment_salphaseion(stream)


def audit(html_path=DEFAULT_HTML):
    # Touches the real page only to confirm the segmentation this audit's
    # content-order distances are derived from has not drifted -- no
    # transform or decode is run against it.
    segments = literal_segments(html_path)
    observed_names = tuple(s.name for s in segments)
    if observed_names != EXPECTED_SEGMENTS:
        raise AssertionError("authenticated SalPhaseIon segment order changed")

    calibration = run_calibration()
    if not calibration["gate_passed"]:
        return {
            "calibration": calibration,
            "role_discrimination": None,
            "verdict": (
                "Calibration gate failed: the scoring rule does not "
                "uniquely rank the known topology of the solved boundaries. "
                "It is not licensed to discriminate Phase 101's roles."
            ),
        }

    role_discrimination = run_role_discrimination()
    return {
        "calibration": calibration,
        "role_discrimination": role_discrimination,
        "verdict": (
            "Inconclusive/model-dependent (corrected same-day, user review). "
            "The calibration gate passed for Phase 3/Phase 3.2, but that "
            "only validates 'explicit consumption vs. checkpoint vs. "
            "order-invariant' -- a different, easier question than the "
            "postpositive/ambiguous attachment thispassword actually poses, "
            "which no solved GSMG boundary calibrates. Two defensible "
            "role modelings (disputed vs. corrected) disagree on the "
            f"winner ({role_discrimination['disputed_ranking']['unique_winner']!r} "
            f"vs. {role_discrimination['corrected_ranking']['unique_winner']!r}). "
            "Phase 101's three thispassword roles remain unresolved; "
            "operand ranking is not licensed."
        ),
    }


FORBIDDEN_OPERAND_NAMES = ("G-ARCH-001",)


def self_test():
    # 1. Calibration gate: linear_consumed uniquely wins for both known
    #    multi-component boundaries, using only structural evidence.
    calibration = run_calibration()
    assert calibration["gate_passed"] is True
    for name, result in calibration["boundaries"].items():
        assert result["unique_winner"] == "linear_consumed", name
        assert result["tie"] is False, name

    # 2. Sanity: the two alternatives calibration rejects are not
    #    themselves degenerate -- they score strictly below linear_consumed
    #    but are not artificially forced to a fixed low score (each
    #    boundary's ordering is independently computed).
    p3_scores = dict(calibration["boundaries"]["phase3"]["ordered"])
    assert p3_scores["linear_consumed"] > p3_scores["order_invariant_consumed"] > p3_scores["unconsumed_checkpoint"]

    # 3. Tie detection is a real, exercised code path -- not merely assumed
    #    absent. Two synthetic equal-score candidates must be reported as a
    #    tie with both names as winners.
    tie_probe = classify_ranking((
        TopologyCandidate("a", True, 0, True, True, 0, 0),
        TopologyCandidate("b", True, 0, True, True, 0, 0),
    ))
    assert tie_probe["tie"] is True
    assert set(tie_probe["winners"]) == {"a", "b"}
    assert tie_probe["unique_winner"] is None

    # 4. Content-distance is computed from the real, currently-authenticated
    #    segmentation, not hardcoded -- confirm the two distances used below
    #    match the page's own literal order.
    assert content_distance("decimal_instruction_2", "hash_prefix") == 1
    assert content_distance("decimal_instruction_2", "faed") == 2

    # 5. The three role names scored here are not retyped -- they must
    #    exactly match salphaseion_operand_binding_audit.py's own generated
    #    password_role values (its own closed 3x3x3x2 family), so a future
    #    change to that axis cannot silently desync from this file.
    page_report = audit_page(DEFAULT_HTML)
    real_password_roles = {m.password_role for m in candidate_models(page_report)}
    for candidate_fn in (role_candidates_disputed, role_candidates_corrected):
        scored_role_names = {c.name for c in candidate_fn()}
        assert scored_role_names == real_password_roles == {
            "password_for_faed", "faed_answer_is_password", "password_for_salph_blob",
        }, candidate_fn.__name__

    # 6. Corrected content-distances: faed_answer_is_password now measures
    #    to lastwordsbeforearchichoice's own output (1 hop, immediately
    #    adjacent), not to raw FAED (2 hops); password_for_salph_blob now
    #    measures to the actual blob segment (2 hops), not to hash_prefix
    #    (1 hop) -- the two referents Phase 372 deliberately separated.
    assert content_distance("decimal_instruction_2", "decimal_instruction_1") == 1
    assert content_distance("decimal_instruction_2", "faed") == 2
    assert content_distance("decimal_instruction_2", "hash_prefix") == 1
    assert content_distance("decimal_instruction_2", "salphaseion_aes_prefix") == 2

    # 7. Calibration analog gap is explicit and asserted, not just narrated.
    assert CALIBRATION_ANALOG_AVAILABLE is False

    # 8. Model-dependence is a checked FACT, not a claim: the disputed
    #    (originally published) modeling and the corrected modeling must
    #    disagree on the winner. If a future edit made them agree, this
    #    assertion would force a conscious decision about whether that
    #    convergence is real progress or a reintroduced bias, rather than
    #    letting the "inconclusive" verdict erode silently.
    report = audit()
    rd = report["role_discrimination"]
    assert rd["disputed_ranking"]["unique_winner"] == "password_for_salph_blob"
    assert rd["corrected_ranking"]["unique_winner"] == "faed_answer_is_password"
    assert rd["models_agree"] is False
    assert rd["operand_ranking_licensed"] is False
    assert rd["operand_ranking_performed"] is False
    assert report["verdict"].startswith("Inconclusive/model-dependent")

    # 9. This audit ranks candidate ROLES, not a VALUE -- guard against
    #    silently reintroducing Phase 372's retracted overclaim (asserting
    #    a specific operand as the sole/required answer) by capping how
    #    often the forbidden name may appear in this file's own source,
    #    all inside explicit disclaimers.
    source = Path(__file__).read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_OPERAND_NAMES:
        occurrences = source.count(forbidden)
        assert occurrences <= 2, (
            f"{forbidden} appears {occurrences} times -- check none of them "
            "assert it as a winning operand"
        )

    print(
        "[*] self-test OK: calibration gate passes for Phase 3/Phase 3.2 "
        "(validates only 'explicit consumption vs. checkpoint vs. "
        "order-invariant', not the postpositive/ambiguous attachment "
        "question thispassword actually poses -- no solved boundary "
        "calibrates that, CALIBRATION_ANALOG_AVAILABLE=False); the "
        "originally-published (disputed) role modeling and a corrected "
        "modeling (fixing the mis-targeted FAED-answer distance, the "
        "hash_prefix/SALPH-blob conflation, and the asymmetric "
        "precedent_match) disagree on the winner "
        f"({rd['disputed_ranking']['unique_winner']!r} vs. "
        f"{rd['corrected_ranking']['unique_winner']!r}) -- confirming the "
        "ranking is model-dependent, not independently-extracted structure. "
        "Verdict: inconclusive; operand_ranking_licensed=False; Phase 101's "
        "three thispassword roles remain unresolved"
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return

    report = audit()
    if args.json:
        print(json.dumps(report, indent=2, default=repr))
        return
    print("-- calibration --")
    for name, result in report["calibration"]["boundaries"].items():
        print(f"  {name}: {result['ordered']} winner={result['unique_winner']}")
    print(f"  gate_passed: {report['calibration']['gate_passed']}")
    if report["role_discrimination"]:
        rd = report["role_discrimination"]
        print("-- role discrimination: disputed (retracted) modeling --")
        for name, score in rd["disputed_ranking"]["ordered"]:
            print(f"  {name}: {score}")
        print(f"  unique_winner: {rd['disputed_ranking']['unique_winner']}")
        print("-- role discrimination: corrected modeling --")
        for name, score in rd["corrected_ranking"]["ordered"]:
            print(f"  {name}: {score}")
        print(f"  unique_winner: {rd['corrected_ranking']['unique_winner']}")
        print(f"  models_agree: {rd['models_agree']}")
        print(f"  operand_ranking_licensed: {rd['operand_ranking_licensed']}")
    print(f"verdict: {report['verdict']}")


if __name__ == "__main__":
    main()
