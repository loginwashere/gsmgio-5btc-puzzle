#!/usr/bin/env python3
"""Candidate-level V2 registry: classifies every candidate the historical 648/650
corpus and Phase 255's 625-candidate menu-gap run produced into core/bounded/
excluded, instead of inheriting a whole source file's label.

The historical 648-candidate corpus (extended_cipher_recheck.CURATED_FILES) is
left untouched -- this module reads it, it never writes it. `curated_v2_core.txt`,
`curated_v2_bounded.txt`, and `curated_v2_full.txt` are generated outputs; never
hand-edit them, regenerate with `--write` after changing the rules below.

Classification is mechanical, derived from metadata this project already
recorded (curated_candidate_corpus_audit.SOURCE_META's direct/bounded/thematic/
mixed/control tiers, excluded_wordlist_coverage_audit.COVERAGE's dedicated-audit
vs medium/broad-input labels), not a fresh per-string editorial read. Two
sources -- full_macro_clue_chain_candidates.txt and
yellowblueprime_matrixsumlist_variants.txt -- are tagged "direct" at the file
level but documented (FINDINGS.md Phase 66/79) as mixing literal creator
anchors with researcher-generated concatenations; those two get a documented
per-candidate override instead of inheriting the file tier uniformly. A
candidate touching several sources with different classes takes the strongest
class among them (core > bounded > excluded) -- an inclusion test ("is there
any documented reason to include this candidate"), not the tier-ranking this
project's Phase 254 review rejected for a different purpose (assigning one
synthetic "primary" descriptive label).
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import answer_forms, keystr_forms  # noqa: E402
from curated_candidate_corpus_audit import SOURCE_META, active_lines, build  # noqa: E402
from extended_cipher_recheck import WORDLIST_DIR, candidate_list_digest  # noqa: E402

WORDLIST_OUT_DIR = WORDLIST_DIR

CLASS_RANK = {"excluded": 0, "bounded": 1, "core": 2}

# Generic old-tier -> V2-class mapping (see SOURCE_META for what each tier means).
TIER_TO_CLASS = {
    "direct": "core",
    "bounded": "bounded",
    "thematic": "excluded",
    "mixed": "excluded",
    "control": "core",
}

# Sources whose V2 class does not follow the generic tier mapping, with the
# documented reason.
SOURCE_CLASS_OVERRIDE = {
    # Bounded tier historically (added only to the opt-in SEED run), but the
    # two candidates are exact leads named explicitly in Phase 253/255 review:
    # they belong in core's "exact SEED leads" bucket, not "bounded".
    "OPENSSL_MENU_GAP_EXACT_CANDIDATES": "core",
    # Mixed tier historically (a legacy list mixing old and new precedent
    # entries), but its role is solved-stage precedent/control material, which
    # core's "solved-stage precedents" bucket exists for.
    "CORE_ALPHABET_SEEDS": "core",
}

# role tags: default is ("passphrase",); these sources add extra roles.
SOURCE_ROLE_TAGS = {
    "VALIDATION_ANSWER": ("control",),
    "CORE_ALPHABET_SEEDS": ("control",),
    "OPENSSL_MENU_GAP_EXACT_CANDIDATES": ("seed",),
}

# Phase 79 (FINDINGS.md): full_macro_clue_chain_candidates.txt's eight literal
# fragments decoded from creator message 8446. Every other line in that file
# is an adjacent pair, cumulative prefix/suffix, or the full chain --
# researcher-generated concatenations of these anchors, not literal text.
FULL_MACRO_CHAIN_ANCHORS = frozenset({
    "yellowblueprimes", "matrixsumlist", "lastwordsbeforearchichoice", "yinyang",
    "wewontgiveawaythepassword", "itsinfrontofyoureyesbutyourenotseeingit",
    "verylaststepisatruegiveaway", "promised",
})
_NUMERIC_RE = re.compile(r"^[\d,]+$")


def _split_source_class_derivation(source, candidate, tier):
    """Return (class, derivation) for one (source, candidate) pair."""
    if source == "full_macro_clue_chain_candidates.txt":
        if candidate in FULL_MACRO_CHAIN_ANCHORS:
            return "core", "literal"
        return "bounded", "concatenation"
    if source == "yellowblueprime_matrixsumlist_variants.txt":
        if _NUMERIC_RE.match(candidate):
            return "core", "mechanical"
        return "bounded", "concatenation"
    if source in SOURCE_CLASS_OVERRIDE:
        return SOURCE_CLASS_OVERRIDE[source], "literal"
    return TIER_TO_CLASS[tier], "literal"


# Phase 255's six menu-gap-scope excluded files, classified by their existing
# excluded_wordlist_coverage_audit.COVERAGE handling label: "dedicated-audit"
# files are standalone, previously-swept candidate lists (Fresco/SafeNet-Luna/
# Looking Forward); "medium-input"/"broad-input" files are intermediate,
# machine-derived text (squashed book-sentence concatenations, filtered chat
# vocabulary) that were never an independently reviewed shortlist, matching
# their pre-existing exclusion category exactly -- no new judgment is applied.
NET_NEW_SOURCE_CLASS = {
    "jacque_fresco_candidates.txt": "bounded",
    "looking_forward_candidates.txt": "bounded",
    "safenet_luna_hsm_candidates.txt": "bounded",
    "content_word_filtered.txt": "excluded",
    "cosmic_duality_book_p6_11_candidates.txt": "excluded",
    "cosmic_duality_book_p8_9.txt": "excluded",
}
NET_NEW_SOURCE_RATIONALE = {
    "jacque_fresco_candidates.txt": "Dedicated exact list (jacque_fresco_wordlist_audit.py, Phases 88-90).",
    "looking_forward_candidates.txt": "Dedicated exact list (yin_yang_transition_audit.py, Phase 44).",
    "safenet_luna_hsm_candidates.txt": "Dedicated exact list (safenet_luna_hsm_audit.py, Phase 116).",
    "content_word_filtered.txt": "Intermediate filtered vocabulary, not a reviewed standalone shortlist.",
    "cosmic_duality_book_p6_11_candidates.txt": "Squashed book-sentence concatenations (medium-corpus Tier 2 input), not literal book text.",
    "cosmic_duality_book_p8_9.txt": "Raw multi-sentence book-page transcription, not single-candidate material.",
}
MENU_GAP_FILES = tuple(NET_NEW_SOURCE_CLASS)

EXPECTED_POOL_COUNT = 1213
EXPECTED_CORE_COUNT = 70
EXPECTED_CORE_DIGEST = "5fb87296c1f04c2b"
EXPECTED_BOUNDED_COUNT = 438
EXPECTED_BOUNDED_DIGEST = "62885ff021a92b07"
EXPECTED_FULL_COUNT = 508
EXPECTED_FULL_DIGEST = "67e389aa7e6a63a9"
EXPECTED_EXCLUDED_COUNT = 705
EXPECTED_FULL_EVALUATIONS = 16056
EXPECTED_FULL_UNIQUE_PASSPHRASES = 14272
EXPECTED_PROMOTED_COUNT = 167
EXPECTED_DEMOTED_COUNT = 34
EXPECTED_REJECTED_COUNT = 705
EXPECTED_RETAINED_HISTORICAL_ONLY_COUNT = 278
EXPECTED_TRANSITIONS = {
    "bounded->bounded": 243,
    "bounded->core": 2,
    "core->bounded": 34,
    "core->core": 64,
    "excluded->bounded": 161,
    "excluded->core": 4,
    "excluded->excluded": 705,
}


def _base_pool():
    """The 650-candidate base pool (648 CURATED_FILES + CORE_ALPHABET_SEEDS +
    VALIDATION_ANSWER + the two Phase-253 exact SEED leads), each row carrying
    its ordered source list and tiers -- reused unmodified from
    curated_candidate_corpus_audit.build(), not recomputed here."""
    report = build(True)
    return report["candidates"]


def _net_new_pool(prior_candidates):
    """The Phase-255 net-new candidates (present in one of the six menu-gap
    files but not the base 650), each row carrying every menu-gap source it
    occurs in, in file-iteration order."""
    prior_set = set(prior_candidates)
    ordered = []
    sources_by_candidate = {}
    for name in MENU_GAP_FILES:
        for value in dict.fromkeys(active_lines(WORDLIST_DIR / name)):
            if value in prior_set:
                continue
            if value not in sources_by_candidate:
                sources_by_candidate[value] = []
                ordered.append(value)
            sources_by_candidate[value].append(name)
    return ordered, sources_by_candidate


def build_registry():
    base_rows = _base_pool()
    base_candidates = tuple(row["candidate"] for row in base_rows)
    net_new_ordered, net_new_sources = _net_new_pool(base_candidates)

    entries = []

    for row in base_rows:
        candidate = row["candidate"]
        sources = row["sources"]
        per_source = [
            (source, *_split_source_class_derivation(source, candidate, SOURCE_META[source][0]))
            for source in sources
        ]
        best_class = max((cls for _s, cls, _d in per_source), key=lambda c: CLASS_RANK[c])
        winners = [(s, d) for s, cls, d in per_source if cls == best_class]
        winning_source, derivation = winners[0]
        roles = ["passphrase"]
        for source in sources:
            for role in SOURCE_ROLE_TAGS.get(source, ()):
                if role not in roles:
                    roles.append(role)
        entries.append({
            "candidate": candidate,
            "sources": sources,
            "class": best_class,
            "class_source": winning_source,
            "derivation": derivation,
            "role": tuple(roles),
            "rationale": SOURCE_META[winning_source][1],
            "pool": "base-650",
            "old_first_source_tier": row["first_source_tier"],
            "old_class": TIER_TO_CLASS[row["first_source_tier"]],
        })

    for candidate in net_new_ordered:
        sources = tuple(net_new_sources[candidate])
        per_source = [(source, NET_NEW_SOURCE_CLASS[source]) for source in sources]
        best_class = max((cls for _s, cls in per_source), key=lambda c: CLASS_RANK[c])
        winning_source = next(s for s, cls in per_source if cls == best_class)
        entries.append({
            "candidate": candidate,
            "sources": sources,
            "class": best_class,
            "class_source": winning_source,
            "derivation": "literal" if best_class == "bounded" else "generated",
            "role": ("passphrase",),
            "rationale": NET_NEW_SOURCE_RATIONALE[winning_source],
            "pool": "phase255-net-new",
            "old_first_source_tier": None,
            "old_class": "excluded",
        })

    return tuple(entries)


def v2_lists(entries):
    core = tuple(e["candidate"] for e in entries if e["class"] == "core")
    bounded = tuple(e["candidate"] for e in entries if e["class"] == "bounded")
    excluded = tuple(e["candidate"] for e in entries if e["class"] == "excluded")
    full = core + bounded
    assert len(set(full)) == len(full), "core and bounded must be disjoint (per-candidate class is unique)"
    return core, bounded, full, excluded


def generated_accounting(candidates):
    generated = []
    for candidate in candidates:
        for form in answer_forms(candidate):
            generated.extend(keystr_forms(form, newline_variants=True))
    return len(generated), len(set(generated))


def promotion_accounting(entries):
    """Compare each candidate's V2 class against the class its old file-level
    tier alone would have implied (TIER_TO_CLASS, with "excluded" standing in
    for candidates that were outside the small corpus entirely). "Promoted"
    means the V2 class ranks higher than the old one (e.g. a literal
    full_macro_clue_chain anchor moving thematic-adjacent obscurity into
    core, or a Fresco/SafeNet-Luna/Looking-Forward line moving from excluded
    to bounded); "demoted" means lower (e.g. a yellowblueprime concatenation
    losing its file's "direct" tier because the string itself is a generated
    variant, not a literal anchor); "retained" means unchanged. Every
    transition is retained here as a queryable, auditable table -- not
    asserted away -- so "promoted"/"rejected"/"retained for historical
    coverage only" can be read off directly instead of re-derived by hand."""
    transitions = Counter()
    promoted, demoted, rejected = [], [], []
    for e in entries:
        old_rank, new_rank = CLASS_RANK[e["old_class"]], CLASS_RANK[e["class"]]
        transitions[(e["old_class"], e["class"])] += 1
        if new_rank > old_rank:
            promoted.append(e["candidate"])
        elif new_rank < old_rank:
            demoted.append(e["candidate"])
        if e["class"] == "excluded":
            rejected.append(e["candidate"])
    return {
        "transitions": {f"{old}->{new}": count for (old, new), count in sorted(transitions.items())},
        "promoted_count": len(promoted),
        "demoted_count": len(demoted),
        "rejected_count": len(rejected),
        "retained_historical_only_count": sum(
            1 for e in entries if e["pool"] == "base-650" and e["class"] == "excluded"
        ),
    }


def report():
    entries = build_registry()
    core, bounded, full, excluded = v2_lists(entries)
    evaluations, unique_passphrases = generated_accounting(full)
    return {
        "pool_count": len(entries),
        "class_counts": dict(Counter(e["class"] for e in entries)),
        "core_count": len(core),
        "core_digest": candidate_list_digest(core),
        "bounded_count": len(bounded),
        "bounded_digest": candidate_list_digest(bounded),
        "full_count": len(full),
        "full_digest": candidate_list_digest(full),
        "excluded_count": len(excluded),
        "full_candidate_form_evaluations": evaluations,
        "full_unique_generated_passphrases": unique_passphrases,
        "promotion_accounting": promotion_accounting(entries),
        "entries": entries,
    }


WORDLIST_HEADER = (
    "# Generated by tools/gsmg/curated_candidate_registry.py -- do not edit by "
    "hand.\n# Regenerate with: python3 tools/gsmg/curated_candidate_registry.py "
    "--write\n"
)


def write_wordlists(rep):
    core, bounded, full, _excluded = (
        rep["_core"], rep["_bounded"], rep["_full"], rep["_excluded"],
    )
    for name, candidates in (
        ("curated_v2_core.txt", core),
        ("curated_v2_bounded.txt", bounded),
        ("curated_v2_full.txt", full),
    ):
        path = WORDLIST_OUT_DIR / name
        path.write_text(WORDLIST_HEADER + "\n".join(candidates) + "\n", encoding="utf-8")
        print(f"[*] wrote {path} ({len(candidates)} candidates)")


def full_report():
    entries = build_registry()
    core, bounded, full, excluded = v2_lists(entries)
    rep = report()
    rep["_core"], rep["_bounded"], rep["_full"], rep["_excluded"] = core, bounded, full, excluded
    return rep


def self_test():
    rep = full_report()
    assert rep["pool_count"] == EXPECTED_POOL_COUNT, rep["pool_count"]
    assert (rep["core_count"], rep["core_digest"]) == (EXPECTED_CORE_COUNT, EXPECTED_CORE_DIGEST)
    assert (rep["bounded_count"], rep["bounded_digest"]) == (EXPECTED_BOUNDED_COUNT, EXPECTED_BOUNDED_DIGEST)
    assert (rep["full_count"], rep["full_digest"]) == (EXPECTED_FULL_COUNT, EXPECTED_FULL_DIGEST)
    assert rep["excluded_count"] == EXPECTED_EXCLUDED_COUNT, rep["excluded_count"]
    assert rep["full_candidate_form_evaluations"] == EXPECTED_FULL_EVALUATIONS
    assert rep["full_unique_generated_passphrases"] == EXPECTED_FULL_UNIQUE_PASSPHRASES
    assert rep["core_count"] + rep["bounded_count"] == rep["full_count"]
    assert rep["core_count"] + rep["bounded_count"] + rep["excluded_count"] == rep["pool_count"]
    core_candidates = {e["candidate"] for e in rep["entries"] if e["class"] == "core"}
    assert "SEED" in core_candidates and "IZLKESEEDQPPEN" in core_candidates
    promo = rep["promotion_accounting"]
    assert promo["promoted_count"] == EXPECTED_PROMOTED_COUNT
    assert promo["demoted_count"] == EXPECTED_DEMOTED_COUNT
    assert promo["rejected_count"] == EXPECTED_REJECTED_COUNT
    assert promo["retained_historical_only_count"] == EXPECTED_RETAINED_HISTORICAL_ONLY_COUNT
    assert promo["transitions"] == EXPECTED_TRANSITIONS
    print(
        f"[*] self-test OK: pool {rep['pool_count']}, core {rep['core_count']}"
        f"/{rep['core_digest']}, bounded {rep['bounded_count']}/{rep['bounded_digest']}, "
        f"full {rep['full_count']}/{rep['full_digest']}, excluded {rep['excluded_count']}"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true", help="write the three curated_v2_*.txt files")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    rep = full_report()
    if args.write:
        write_wordlists(rep)
        return
    if args.json:
        entries = rep.pop("entries")
        print(json.dumps(rep, indent=2))
        print(json.dumps(entries, indent=2))
        return
    print(f"pool: {rep['pool_count']}")
    print(f"class counts: {rep['class_counts']}")
    print(f"core: {rep['core_count']} / {rep['core_digest']}")
    print(f"bounded: {rep['bounded_count']} / {rep['bounded_digest']}")
    print(f"full: {rep['full_count']} / {rep['full_digest']}")
    print(f"excluded: {rep['excluded_count']}")
    print(f"full generated evaluations: {rep['full_candidate_form_evaluations']}")
    print(f"full unique passphrases: {rep['full_unique_generated_passphrases']}")


if __name__ == "__main__":
    main()
