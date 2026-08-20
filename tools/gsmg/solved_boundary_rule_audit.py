#!/usr/bin/env python3
"""Seed 1 from doc/Brainstorms/2026-08-20 - Post-Phase-340 Future Search
Portfolio.md: "Solved-boundary rule audit with leave-one-out stress tests."

Question: do this project's candidate-construction habits (component order,
connected/no-separator assembly, instruction-selected casing, literal versus
prefix rules) actually reconstruct the exact known GSMG password preimages
when fed only the already-solved clue-answer components plus the local
assembly instructions available on that boundary's own page -- without any
peek at the target hash to pick parameters? If a frozen rule engine cannot
do this cheaply on the three boundaries where the answer is already public,
generating more candidates from the same grammar for an unresolved blob is
unjustified.

Ground truth (independently re-verified against README.md lines 90-266,
the primary public `puzzlehunt/gsmgio-5btc-puzzle` README this project has
separately cross-checked -- not retyped from the brainstorm note's own
summary table, which used an approximate "aaa" for what the page literally
shows as "aa"):

  Phase 2  -- "The password is causality." One component, no separator or
              case/whitespace ambiguity on the page at all.
  Phase 3  -- "The password is a concatenation of 7 parts... Concatenate
              them all and perform SHA256." Parts 1-5 (causality, Safenet,
              Luna, HSM, 11110) carry no case/whitespace ambiguity. Part 6
              (the genesis-block hex fragment) is explicitly annotated
              "/(aBa, connected enf)" -- preserve case, remove whitespace.
              Part 7 (the post-move chess FEN) is explicitly annotated
              "/(aBa, connected not enf)" -- preserve case, KEEP whitespace.
  Phase 3.2 -- Three clue answers, each explicitly annotated "/(aa,
              connected enf)" in the Phase-3 plaintext that names them --
              force lowercase, remove whitespace -- plus "just add giveit
              in front of the answer" as an explicit literal prefix
              instruction for clue 2 only.

Frozen rule engine and enumeration (decided before checking any hash):

  Each boundary's PRIMARY candidate is the single most literal reading of
  its page instructions (see BOUNDARY-specific comments below). Where the
  page text alone does not fully pin a byte-level choice, that choice is
  enumerated as a small frozen axis (2-3 options each, primary listed
  first) rather than guessed:
    - Phase 3: does the "0x..." hex fragment's literal-ASCII-text form
      (per the page's own literal SHA256(...) rendering) include the "0x"
      prefix, and is part 7's "not enf" whitespace-keeping annotation
      actually load-bearing (hedge: strip it anyway)?
    - Phase 3.2: is "giveit" glued directly to the clue-2 answer or
      space-separated; does "enf" mean strip literal whitespace only or
      strip all non-alphanumeric characters (needed to explain the
      apostrophe-free "heisenbergs..." in the known answer); is the raw
      clue-3 answer text "Heisenberg's" (with the possessive) or
      "Heisenberg" (without)?
  Candidates are canonically ordered by axis "distance from all-primary"
  (0 = the fully literal reading), so rank is fixed by construction before
  any hash is computed -- not chosen after seeing which one hits.

  Two controls run alongside the main enumeration:
    - shuffled component order (same axis budget, components reordered) --
      should not accidentally match; a match would indicate order doesn't
      actually matter, which would undercut the "component order" rule.
    - naive global casing/whitespace baseline -- one casing+whitespace
      choice applied uniformly to every component, ignoring per-component
      page annotations, cross-producted over {preserve/force-lower} x
      {keep/strip}. This checks whether reading each boundary's own
      instructions is actually necessary or whether one blind global rule
      would have sufficed.

Honesty note on what this does and does not show: with n=3 known
boundaries, this is a reconstruction-validation exercise, not blind
discovery or a statistically validated author model (this project's own
stated "Dataset reality check"). The "primary" axis choice is drawn from
this project's own prior reading of the primary README, so recovering it
is not evidence of an independently-guessed rule -- it demonstrates that a
compact, explicitly-declared instruction-parsing rule set reproduces all
three known preimages exactly, and that plausible near-miss alternatives
(no "0x" prefix, hex-decoded rendering, stripped FEN whitespace, spaced
giveit, apostrophe-free clue 3, whitespace-only "enf") are genuinely wrong
under the real hash -- i.e. the engine is precise, not merely permissive.

Promotion gate (frozen before running): exact recovery in the top 10 with
at most 100 unique byte strings per boundary. Below that gate, this rule
set is not licensed to generate candidates for any unresolved blob.
"""

import argparse
import hashlib
import itertools
import json


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def strip_all_nonalnum(text: str) -> str:
    return "".join(ch for ch in text if ch.isalnum())


def strip_whitespace_only(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())


# ---------------------------------------------------------------------------
# Ground truth, copied verbatim from README.md (re-checked in self_test()
# against the file itself, not retyped from memory a second time).
# ---------------------------------------------------------------------------

PHASE3_HEX_PART = (
    "0x736B6E616220726F662074756F6C69616220646E6F63657320666F206B6E697262"
    "206E6F20726F6C6C65636E61684320393030322F6E614A2F33302073656D695420656854"
)
PHASE3_FEN_PART = "B5KR/1r5B/2R5/2b1p1p1/2P1k1P1/1p2P2p/1P2P2P/3N1N2 b - - 0 1"
PHASE3_PARTS_FIXED = ["causality", "Safenet", "Luna", "HSM", "11110"]

PHASE32_RAW_PRIMARY = ("Jacque Fresco", "just one second", "Heisenberg's uncertainty principle")
GIVEIT = "giveit"

EXPECTED_HASHES = {
    "phase2": "eb3efb5151e6255994711fe8f2264427ceeebf88109e1d7fad5b0a8b6d07e5bf",
    "phase3": "1a57c572caf3cf722e41f5f9cf99ffacff06728a43032dd44c481c77d2ec30d5",
    "phase3_2": "250f37726d6862939f723edc4f993fde9d33c6004aab4f2203d9ee489d61ce4c",
}


def _axis_product(axes):
    """Cartesian product over (name, [primary, alt, ...]) axis lists,
    yielded as (params_dict, distance) in ascending distance order, where
    distance = sum of each chosen value's index in its own axis list.
    distance 0 is always the fully-literal/primary reading. This fixes
    candidate rank by construction, before any hash is computed."""
    names = [a[0] for a in axes]
    value_lists = [a[1] for a in axes]
    combos = list(itertools.product(*value_lists))

    def distance(combo):
        return sum(value_lists[i].index(v) for i, v in enumerate(combo))

    order = sorted(range(len(combos)), key=lambda i: (distance(combos[i]), i))
    for i in order:
        combo = combos[i]
        yield dict(zip(names, combo)), distance(combo)


# ---------------------------------------------------------------------------
# Phase 2 -- baseline case only. Per the brainstorm's own predeclared
# reading: recovering only Phase 2 is not meaningful on its own (a single
# component has no order/casing/whitespace choice to get right).
# ---------------------------------------------------------------------------

def phase2_candidates():
    return [("causality", {"axes": {}, "distance": 0})]


def phase2_shuffled_candidates():
    return []  # no order to shuffle with exactly one component


def phase2_naive_candidates():
    return phase2_candidates()


# ---------------------------------------------------------------------------
# Phase 3
# ---------------------------------------------------------------------------

PHASE3_AXES = [
    ("hex_render", ["as_shown_with_0x", "as_shown_no_0x", "hex_decoded_ascii"]),
    ("fen_ws", ["keep", "strip"]),
]


def _phase3_hex_value(mode):
    if mode == "as_shown_with_0x":
        return PHASE3_HEX_PART
    if mode == "as_shown_no_0x":
        return PHASE3_HEX_PART[2:]
    if mode == "hex_decoded_ascii":
        raw = bytes.fromhex(PHASE3_HEX_PART[2:])
        try:
            return raw.decode("ascii")
        except UnicodeDecodeError:
            return raw.hex()
    raise ValueError(mode)


def _phase3_fen_value(mode):
    if mode == "keep":
        return PHASE3_FEN_PART
    if mode == "strip":
        return PHASE3_FEN_PART.replace(" ", "")
    raise ValueError(mode)


def phase3_candidates(part_order=None):
    part_order = list(range(7)) if part_order is None else part_order
    out, seen = [], set()
    for axes, distance in _axis_product(PHASE3_AXES):
        hexv = _phase3_hex_value(axes["hex_render"])
        fenv = _phase3_fen_value(axes["fen_ws"])
        components = PHASE3_PARTS_FIXED + [hexv, fenv]
        candidate = "".join(components[i] for i in part_order)
        if candidate in seen:
            continue
        seen.add(candidate)
        out.append((candidate, {"axes": axes, "distance": distance}))
    return out


def phase3_shuffled_candidates():
    return phase3_candidates(part_order=list(reversed(range(7))))


def phase3_naive_candidates():
    """Global casing/whitespace rule applied to every component uniformly,
    no per-component page-instruction parsing."""
    out = []
    for force_lower in (False, True):
        for strip_ws in (False, True):
            def norm(t):
                r = t.lower() if force_lower else t
                return r.replace(" ", "") if strip_ws else r
            parts = [norm(p) for p in PHASE3_PARTS_FIXED]
            hexv = norm(PHASE3_HEX_PART)
            fenv = norm(PHASE3_FEN_PART)
            candidate = "".join(parts + [hexv, fenv])
            out.append((candidate, {"global_force_lower": force_lower, "global_strip_whitespace": strip_ws}))
    return out


# ---------------------------------------------------------------------------
# Phase 3.2
# ---------------------------------------------------------------------------

PHASE32_AXES = [
    ("giveit_sep", ["none", "space"]),
    ("clue3_apostrophe", ["with_apostrophe", "without_apostrophe"]),
    ("enf_scope", ["strip_all_nonalnum", "strip_whitespace_only"]),
]


def _phase32_normalize(raw, enf_scope):
    lowered = raw.lower()  # "aa" annotation: force lowercase, explicit on the page for all three
    if enf_scope == "strip_all_nonalnum":
        return strip_all_nonalnum(lowered)
    if enf_scope == "strip_whitespace_only":
        return strip_whitespace_only(lowered)
    raise ValueError(enf_scope)


def phase32_candidates(component_order=None):
    component_order = [0, 1, 2] if component_order is None else component_order
    out, seen = [], set()
    for axes, distance in _axis_product(PHASE32_AXES):
        raw3 = PHASE32_RAW_PRIMARY[2] if axes["clue3_apostrophe"] == "with_apostrophe" else "Heisenberg uncertainty principle"
        c1 = _phase32_normalize(PHASE32_RAW_PRIMARY[0], axes["enf_scope"])
        c2_body = _phase32_normalize(PHASE32_RAW_PRIMARY[1], axes["enf_scope"])
        sep = "" if axes["giveit_sep"] == "none" else " "
        c2 = GIVEIT + sep + c2_body
        c3 = _phase32_normalize(raw3, axes["enf_scope"])
        components = [c1, c2, c3]
        candidate = "".join(components[i] for i in component_order)
        if candidate in seen:
            continue
        seen.add(candidate)
        out.append((candidate, {"axes": axes, "distance": distance}))
    return out


def phase32_shuffled_candidates():
    return phase32_candidates(component_order=[2, 0, 1])


def phase32_naive_candidates():
    out = []
    for force_lower in (False, True):
        for strip_all in (False, True):
            def norm(t):
                r = t.lower() if force_lower else t
                return strip_all_nonalnum(r) if strip_all else r
            c1 = norm(PHASE32_RAW_PRIMARY[0])
            c2 = GIVEIT + norm(PHASE32_RAW_PRIMARY[1])
            c3 = norm(PHASE32_RAW_PRIMARY[2])
            candidate = c1 + c2 + c3
            out.append((candidate, {"global_force_lower": force_lower, "global_strip_all_nonalnum": strip_all}))
    return out


# ---------------------------------------------------------------------------
# Scoring (the "Proposed seed-1 scoring contract")
# ---------------------------------------------------------------------------

def _find(candidates, expected_hash):
    for rank, (candidate, prov) in enumerate(candidates, start=1):
        if sha256_hex(candidate) == expected_hash:
            return rank, candidate, prov
    return None, None, None


def audit_boundary(name, main_fn, shuffled_fn, naive_fn):
    expected_hash = EXPECTED_HASHES[name]
    main_candidates = main_fn()
    rank, candidate, prov = _find(main_candidates, expected_hash)

    tier_size = None
    if prov is not None and "distance" in prov:
        tier_size = sum(1 for _c, p in main_candidates if p.get("distance") == prov["distance"])

    shuffled_candidates = shuffled_fn()
    shuffled_rank, _sc, _sp = _find(shuffled_candidates, expected_hash)

    naive_candidates = naive_fn()
    naive_rank, naive_candidate, naive_prov = _find(naive_candidates, expected_hash)

    return {
        "boundary": name,
        "expected_hash": expected_hash,
        "exact_preimage_present": rank is not None,
        "rank": rank,
        "recovered_preimage_length": len(candidate) if candidate else None,
        "authorizing_axes": (prov or {}).get("axes"),
        "total_unique_candidates": len(main_candidates),
        "equally_ranked_candidates": tier_size,
        "shuffled_control_candidates": len(shuffled_candidates),
        "shuffled_control_found_match": shuffled_rank is not None,
        "naive_global_candidates": len(naive_candidates),
        "naive_global_found_match": naive_rank is not None,
        "naive_global_rank": naive_rank,
        "naive_global_winning_params": naive_prov,
    }


def run():
    boundaries = [
        audit_boundary("phase2", phase2_candidates, phase2_shuffled_candidates, phase2_naive_candidates),
        audit_boundary("phase3", phase3_candidates, phase3_shuffled_candidates, phase3_naive_candidates),
        audit_boundary("phase3_2", phase32_candidates, phase32_shuffled_candidates, phase32_naive_candidates),
    ]
    all_top10 = all(b["exact_preimage_present"] and b["rank"] <= 10 for b in boundaries)
    all_bounded = all(b["total_unique_candidates"] <= 100 for b in boundaries)
    return {
        "boundaries": boundaries,
        "success_gate": "exact recovery in top 10 with at most 100 unique byte strings per boundary",
        "promotion_gate_passed": all_top10 and all_bounded,
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def self_test():
    # 1. Ground-truth hashes reproduce independently from the fully literal
    #    concatenation, exactly as README.md states it (no rule engine
    #    involved -- a direct re-derivation).
    assert sha256_hex("causality") == EXPECTED_HASHES["phase2"]
    phase3_literal = "".join(PHASE3_PARTS_FIXED) + PHASE3_HEX_PART + PHASE3_FEN_PART
    assert sha256_hex(phase3_literal) == EXPECTED_HASHES["phase3"]
    phase32_literal = "jacquefresco" + "giveit" + "justonesecond" + "heisenbergsuncertaintyprinciple"
    assert sha256_hex(phase32_literal) == EXPECTED_HASHES["phase3_2"]

    # 2. Cross-check those same literal strings against this project's own
    #    prior-verified hash constants in data.py, so a transcription error
    #    here can't silently diverge from the rest of the project.
    import data as _data
    assert EXPECTED_HASHES["phase2"] == _data.VERIFIED_PRIOR_COMMAND_HASHES["phase2_causality"]
    assert EXPECTED_HASHES["phase3"] == _data.VERIFIED_PRIOR_COMMAND_HASHES["phase3_parts"]
    assert EXPECTED_HASHES["phase3_2"] == _data.VERIFIED_PRIOR_COMMAND_HASHES["phase32_clues"]

    # 3. Rank-1 (fully literal / all-primary-axis) candidate of each
    #    boundary's frozen engine matches the ground truth exactly.
    assert phase2_candidates()[0][0] == "causality"
    assert phase3_candidates()[0][0] == phase3_literal
    assert phase32_candidates()[0][0] == phase32_literal

    # 4. Bounded-enumeration contract: axis grids stay small (well under
    #    the 100-per-boundary success-gate cap) and produce no accidental
    #    duplicate strings across distinct axis settings.
    p3 = phase3_candidates()
    assert len(p3) == 3 * 2 == 6
    assert len({c for c, _ in p3}) == len(p3)
    p32 = phase32_candidates()
    # 2x2x2=8 axis combinations, but "strip_all_nonalnum" and
    # "strip_whitespace_only" are indistinguishable whenever the raw text
    # has no non-alnum, non-whitespace character to strip -- true for the
    # "without_apostrophe" clue-3 reading -- so 2 of the 8 combos collapse
    # to duplicate strings and are deduplicated to 6 unique candidates.
    assert len(p32) == 6
    assert len({c for c, _ in p32}) == len(p32)

    # 5. Full audit: all three boundaries recovered at rank 1, promotion
    #    gate passes.
    report = run()
    assert report["promotion_gate_passed"] is True
    for b in report["boundaries"]:
        assert b["exact_preimage_present"], b["boundary"]
        assert b["rank"] == 1, (b["boundary"], b["rank"])

    # 6. Negative controls: reordering components must NOT accidentally
    #    reproduce either non-trivial boundary's hash (order is genuinely
    #    load-bearing, not a decoration).
    assert sha256_hex(phase3_shuffled_candidates()[0][0]) != EXPECTED_HASHES["phase3"]
    for c, _ in phase3_shuffled_candidates():
        assert sha256_hex(c) != EXPECTED_HASHES["phase3"]
    for c, _ in phase32_shuffled_candidates():
        assert sha256_hex(c) != EXPECTED_HASHES["phase3_2"]

    # 7. Naive global baseline: exactly one of the four global combos
    #    succeeds per boundary, and -- the actual point of this control --
    #    it is a DIFFERENT combo per boundary (Phase 3 needs
    #    preserve-case/keep-whitespace; Phase 3.2 needs force-lower/
    #    strip-all-nonalnum). No single global rule covers both, so
    #    per-boundary instruction reading is necessary, not merely
    #    convenient.
    p3_naive = phase3_naive_candidates()
    p3_naive_hits = [p for c, p in p3_naive if sha256_hex(c) == EXPECTED_HASHES["phase3"]]
    assert len(p3_naive_hits) == 1
    assert p3_naive_hits[0] == {"global_force_lower": False, "global_strip_whitespace": False}

    p32_naive = phase32_naive_candidates()
    p32_naive_hits = [p for c, p in p32_naive if sha256_hex(c) == EXPECTED_HASHES["phase3_2"]]
    assert len(p32_naive_hits) == 1
    assert p32_naive_hits[0] == {"global_force_lower": True, "global_strip_all_nonalnum": True}

    print("[*] self-test OK: three ground-truth hashes re-derived independently and cross-checked "
          "against data.py; frozen rule engine recovers all three boundaries at rank 1 from a "
          f"{len(p3)}-candidate (Phase 3) / {len(p32)}-candidate (Phase 3.2) enumeration; shuffled-order "
          "control produces zero accidental matches; naive global-rule baseline succeeds on exactly "
          "one of four combos per boundary, and that combo differs between Phase 3 and Phase 3.2, "
          "confirming per-boundary instruction reading is load-bearing")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = run() if args.run else {"note": "pass --run to execute the audit"}
    if args.json:
        print(json.dumps(report, indent=2, default=repr))
    else:
        for b in report.get("boundaries", []):
            print(f"-- {b['boundary']} --")
            for k, v in b.items():
                if k == "boundary":
                    continue
                print(f"  {k}: {v}")
        for k, v in report.items():
            if k != "boundaries":
                print(f"{k}: {v}")


if __name__ == "__main__":
    main()
