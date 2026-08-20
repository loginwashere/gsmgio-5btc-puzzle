#!/usr/bin/env python3
"""Audit the exact composition and provenance of extended_cipher_recheck's corpus.

This is a corpus audit, not a decryptor.  It explains what "648 curated
candidates" means, preserves source order, attributes every candidate to every
source in which it occurs, and distinguishes exact-string deduplication from
normalization-equivalent and generated-passphrase duplication.
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import answer_forms, keystr_forms  # noqa: E402
from data import VALIDATION_ANSWER  # noqa: E402
from extended_cipher_recheck import (  # noqa: E402
    CURATED_FILES,
    OPENSSL_MENU_GAP_EXACT_CANDIDATES,
    WORDLIST_DIR,
    candidate_list_digest,
    load_curated_candidates,
)
from matrixsum_permutation_sweep import CORE_ALPHABET_SEEDS  # noqa: E402


# Strength describes provenance/selection, not whether the candidate is correct.
# "direct" means creator-authored/authenticated or mechanically fixed puzzle data;
# "bounded" means a limited interpretation of real clues or primary sources;
# "thematic" means franchise/book/wiki vocabulary with weak local selection;
# "control" means solved material retained as precedent or a sanity candidate.
SOURCE_META = {
    "last_command.txt": ("direct", "Authenticated last-command/hash vocabulary and bounded terminal-command renderings."),
    "salphaseion_own_keywords_combined.txt": ("bounded", "All order/spacing forms of four literal SalPhaseIon page tokens; token source is direct, ordering is not."),
    "single_fragments.txt": ("direct", "Small set of literal creator/page fragments reused as alphabet or keystream seeds."),
    "other_half_candidates.txt": ("bounded", "Cosmic Duality primary-text phrases connected to the solved HALF AND BETTER HALF plaintext."),
    "three_sexes_candidates.txt": ("bounded", "Plato/three-sexes phrases from the Cosmic Duality source-text lane."),
    "hegel_marx_candidates.txt": ("thematic", "Dialectic and religious-duality vocabulary; conceptually related but weakly selected at the boundary."),
    "original_riddle_candidates.txt": ("thematic", "Researcher-composed riddle sentences, not creator text; intended to mimic the earlier riddle-alphabet mechanism."),
    "discovered_paths.txt": ("bounded", "Real archived paths plus tightly related path/quote forms found during Wayback enumeration."),
    "yellowblueprime_matrixsumlist_variants.txt": ("direct", "Authenticated macro-clue anchors plus researcher-generated spacing, punctuation, ordering, and singular/plural variants; the file-level bucket is not a claim that every full string is literal creator text."),
    "phrases.txt": ("mixed", "Legacy master list mixing solved plaintext, creator clues, page titles, lore, and historical chat phrases."),
    "phrases-joined.txt": ("mixed", "Joined/normalized companions to the legacy phrase list; mostly representation coverage."),
    "riddle_combinations.txt": ("bounded", "Hand-bounded concatenations of authenticated clue anchors and a few explicit creator hints."),
    "yinyang_matrix_symbolism.txt": ("thematic", "Matrix-franchise yin/yang interpretations and film-analysis vocabulary."),
    "architect_coded.txt": ("thematic", "Architect/order side of a researcher-defined Architect-versus-Oracle vocabulary split."),
    "architect_gnostic_synonyms.txt": ("bounded", "Gnostic vocabulary motivated by creator remarks, expanded through external reference research."),
    "architect_wiki_deepdive.txt": ("thematic", "Matrix wiki and linked mythology/trivia vocabulary; broad external expansion."),
    "oracle_coded.txt": ("thematic", "Oracle/change side of the researcher-defined split; entirely duplicated by earlier files in current load order."),
    "matrix_trilogy.txt": ("thematic", "Broad franchise names, objects, places, ships, and quotations."),
    "blockchain_metadata_candidates.txt": ("bounded", "Independently verified address/transaction fields and clue-bounded address halves."),
    "first_piece_color_candidates.txt": ("direct", "Mechanically reproduced first-piece bit, RGB, hex, decimal, and prime values."),
    "matrixsumlist_choice_candidates.txt": ("bounded", "Exact 574061/Architect-choice reconstruction outputs plus narrowly proposed edge readings."),
    "fefe_plated_seed_candidates.txt": ("thematic", "Four predeclared literal FE coatings of SEED from the unconfirmed Fe-plated rebus."),
    "full_macro_clue_chain_candidates.txt": ("direct", "Creator message 8446 supplies the anchors; adjacent pairs, cumulative prefixes/suffixes, and the full chain are researcher-generated combinations retained in the historical file-level bucket."),
    "CORE_ALPHABET_SEEDS": ("mixed", "Small in-code precedent list used by matrixsum permutation work; only two entries are new here."),
    "VALIDATION_ANSWER": ("control", "Known solved 3.2.2 plaintext; already duplicated through CORE_ALPHABET_SEEDS."),
    "OPENSSL_MENU_GAP_EXACT_CANDIDATES": ("bounded", "Literal SEED and recovered historical IZLKESEEDQPPEN, added only to the SEED cipher run."),
}

# Every on-disk wordlist that is deliberately outside CURATED_FILES.  This is
# an explicit scope manifest, not a claim that these sources were unavailable
# when the loader was created.  Most coexisted with it from the initial toolkit
# import; they were excluded because they are broad/generated inputs or because
# a dedicated audit owns their coverage.
EXCLUDED_WORDLISTS = {
    "anchor_x_vocab_combos.txt": ("medium-input", "Large generated combination set; incorporated into the separate medium-corpus Tier 2 workflow."),
    "chat_mined_lines.txt": ("broad-input", "Raw community-chat lines; intentionally outside the small distilled corpus."),
    "chat_mined_words.txt": ("broad-input", "Raw community-chat vocabulary; handled only through broader filtered sweeps."),
    "chat_theme_content_words.txt": ("medium-input", "Generated chat-theme reductions incorporated into medium-corpus Tier 2."),
    "chat_theme_lines_raw.txt": ("broad-input", "Broad community-chat material used as an input to medium curation."),
    "content_word_filtered.txt": ("broad-input", "Intermediate filtered vocabulary rather than a reviewed standalone shortlist."),
    "cosmic_duality_book_candidates.txt": ("medium-input", "Large book-derived candidate set incorporated into medium-corpus Tier 2."),
    "cosmic_duality_book_full_text.txt": ("broad-input", "Primary-text extraction used by targeted and medium-corpus tooling, not a password shortlist."),
    "cosmic_duality_book_p6_11_candidates.txt": ("medium-input", "Book-page derivations incorporated into medium-corpus Tier 2."),
    "cosmic_duality_book_p8_9.txt": ("medium-input", "Book-page transcription incorporated into the separate medium-corpus workflow."),
    "cosmic_duality_book_screenshot_ocr.txt": ("broad-input", "Raw screenshot OCR incorporated into medium-corpus Tier 1 after normalization."),
    "jacque_fresco_candidates.txt": ("dedicated-audit", "Swept separately by jacque_fresco_wordlist_audit.py in Phases 88-90."),
    "macro_clue_permutation_combinations.txt": ("dedicated-audit", "P(8,k) k=1-7 order-sensitive combinations of the 8 creator-authored macro-clue fragments; swept separately via the dedicated GPU AES/KDF oracle (tools/gpu_oracle) against all 4 tracked blobs in Phase 322; disposition rejected."),
    "macro_clue_permutation_combinations_k8.txt": ("dedicated-audit", "The k=8 case (all 8 fragments, no subset choice) Phase 322 deliberately omitted and reopened explicitly; swept separately via the same dedicated GPU oracle in Phase 334; disposition rejected."),
    "looking_forward_candidates.txt": ("dedicated-audit", "Swept separately by yin_yang_transition_audit.py; also incorporated into medium-corpus Tier 2."),
    "matrix_architect_scene_through_choice_words.txt": ("dedicated-audit", "A cached 1,326-word scene stored on one active line and consumed by salt_selector_permutation_audit.py, not a one-candidate shortlist."),
    "matrix_script_windows.txt": ("broad-input", "464,586 overlapping screenplay windows; intentionally bounded by later medium-corpus filtering."),
    "matrix_scripts_words.txt": ("broad-input", "Broad screenplay vocabulary used as a medium-corpus input."),
    "medium_curated_all.txt": ("generated-output", "Generated combined medium-corpus output with its own digest and checkpointed sweeps."),
    "medium_curated_provenance.txt": ("generated-output", "Generated provenance sidecar, not a candidate source."),
    "medium_curated_tier1_primary.txt": ("generated-output", "Generated medium-corpus Tier 1 output swept separately."),
    "medium_curated_tier2_derived.txt": ("generated-output", "Generated medium-corpus Tier 2 output swept separately."),
    "medium_curated_tier3_broad.txt": ("generated-output", "Generated medium-corpus Tier 3 output, outside the small-corpus boundary."),
    "safenet_luna_hsm_candidates.txt": ("dedicated-audit", "Swept separately by safenet_luna_hsm_audit.py."),
    "session_combined_for_chain.txt": ("medium-input", "Large generated chain-combination set incorporated into medium-corpus Tier 2."),
    "curated_v2_core.txt": ("generated-output", "Generated by curated_candidate_registry.py (candidate-level V2 core class); this historical 648/650 corpus is intentionally left unmerged with it."),
    "curated_v2_bounded.txt": ("generated-output", "Generated by curated_candidate_registry.py (candidate-level V2 bounded class); this historical 648/650 corpus is intentionally left unmerged with it."),
    "curated_v2_full.txt": ("generated-output", "Generated by curated_candidate_registry.py (V2 core+bounded union); this historical 648/650 corpus is intentionally left unmerged with it."),
}

EXPECTED_BASE_COUNT = 648
EXPECTED_BASE_DIGEST = "2d233645ef49a141"
EXPECTED_SEED_COUNT = 650
EXPECTED_SEED_DIGEST = "ab8252005a8388f5"

EXPECTED_SOURCE_ACCOUNTING = {
    "last_command.txt": (16, 16, 16, 0),
    "salphaseion_own_keywords_combined.txt": (48, 48, 48, 0),
    "single_fragments.txt": (17, 17, 17, 0),
    "other_half_candidates.txt": (22, 22, 22, 0),
    "three_sexes_candidates.txt": (12, 12, 12, 0),
    "hegel_marx_candidates.txt": (14, 14, 14, 0),
    "original_riddle_candidates.txt": (24, 24, 24, 0),
    "discovered_paths.txt": (49, 49, 48, 1),
    "yellowblueprime_matrixsumlist_variants.txt": (25, 25, 25, 0),
    "phrases.txt": (83, 83, 69, 14),
    "phrases-joined.txt": (25, 25, 11, 14),
    "riddle_combinations.txt": (55, 55, 55, 0),
    "yinyang_matrix_symbolism.txt": (20, 20, 20, 0),
    "architect_coded.txt": (31, 31, 30, 1),
    "architect_gnostic_synonyms.txt": (47, 47, 22, 25),
    "architect_wiki_deepdive.txt": (35, 35, 30, 5),
    "oracle_coded.txt": (26, 26, 0, 26),
    "matrix_trilogy.txt": (114, 114, 103, 11),
    "blockchain_metadata_candidates.txt": (22, 22, 22, 0),
    "first_piece_color_candidates.txt": (20, 20, 20, 0),
    "matrixsumlist_choice_candidates.txt": (14, 14, 14, 0),
    "fefe_plated_seed_candidates.txt": (4, 4, 4, 0),
    "full_macro_clue_chain_candidates.txt": (30, 27, 20, 7),
    "CORE_ALPHABET_SEEDS": (11, 11, 2, 9),
    "VALIDATION_ANSWER": (1, 1, 0, 1),
}

EXPECTED_BASE_HEADLINES = {
    "active_source_lines": 765,
    "source_count": 25,
    "multi_source_candidate_count": 94,
    "cross_source_tier_candidate_count": 64,
    "oracle_overlap_groups": 104,
    "oracle_overlap_candidates": 245,
    "shared_generated_passphrases": 1973,
    "candidate_form_evaluations": 17037,
    "unique_generated_passphrases": 14551,
    "duplicate_generated_evaluations": 2486,
}


def active_lines(path):
    return tuple(
        line.strip()
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.strip() and not line.strip().startswith("#")
    )


def wordlist_manifest():
    """Account for every .txt wordlist as included or explicitly excluded."""
    disk_names = {path.name for path in WORDLIST_DIR.glob("*.txt")}
    included_names = set(CURATED_FILES)
    excluded_names = set(EXCLUDED_WORDLISTS)
    if included_names & excluded_names:
        raise AssertionError("wordlist manifest includes a file in both scopes")
    if disk_names != included_names | excluded_names:
        missing = sorted(disk_names - included_names - excluded_names)
        stale = sorted((included_names | excluded_names) - disk_names)
        raise AssertionError(
            f"wordlist manifest drift: unclassified={missing}, missing_on_disk={stale}"
        )
    rows = []
    for name in sorted(disk_names):
        values = active_lines(WORDLIST_DIR / name)
        if name in included_names:
            rows.append({
                "source": name,
                "status": "included",
                "category": "curated-file",
                "active_lines": len(values),
                "rationale": SOURCE_META[name][1],
            })
        else:
            category, rationale = EXCLUDED_WORDLISTS[name]
            rows.append({
                "source": name,
                "status": "excluded",
                "category": category,
                "active_lines": len(values),
                "rationale": rationale,
            })
    return tuple(rows)


def oracle_overlap(candidate_passphrases, ordered):
    """Measure candidate overlap using the passphrases the oracle really sees."""
    passphrase_candidates = defaultdict(list)
    for candidate in ordered:
        for passphrase in candidate_passphrases[candidate]:
            passphrase_candidates[passphrase].append(candidate)

    shared = {
        passphrase: candidates
        for passphrase, candidates in passphrase_candidates.items()
        if len(candidates) > 1
    }
    parent = {candidate: candidate for candidate in ordered}

    def find(candidate):
        while parent[candidate] != candidate:
            parent[candidate] = parent[parent[candidate]]
            candidate = parent[candidate]
        return candidate

    def union(left, right):
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for candidates in shared.values():
        for candidate in candidates[1:]:
            union(candidates[0], candidate)

    members = {candidate for candidates in shared.values() for candidate in candidates}
    groups = defaultdict(list)
    for candidate in ordered:
        if candidate in members:
            groups[find(candidate)].append(candidate)
    return len(shared), tuple(tuple(group) for group in groups.values())


def build(include_seed=False):
    seen = set()
    ordered = []
    provenance = defaultdict(list)
    source_rows = []

    sources = [(name, active_lines(WORDLIST_DIR / name)) for name in CURATED_FILES]
    sources.extend((
        ("CORE_ALPHABET_SEEDS", tuple(CORE_ALPHABET_SEEDS)),
        ("VALIDATION_ANSWER", (VALIDATION_ANSWER,)),
    ))
    if include_seed:
        sources.append(("OPENSSL_MENU_GAP_EXACT_CANDIDATES", tuple(OPENSSL_MENU_GAP_EXACT_CANDIDATES)))

    for source, values in sources:
        local_unique = tuple(dict.fromkeys(values))
        before = len(ordered)
        for value in values:
            if source not in provenance[value]:
                provenance[value].append(source)
            if value not in seen:
                seen.add(value)
                ordered.append(value)
        tier, rationale = SOURCE_META[source]
        source_rows.append({
            "source": source,
            "tier": tier,
            "active_lines": len(values),
            "unique_in_source": len(local_unique),
            "new_exact": len(ordered) - before,
            "duplicate_of_prior": len(local_unique) - (len(ordered) - before),
            "rationale": rationale,
        })

    generated = []
    candidate_passphrases = {}
    for candidate in ordered:
        candidate_generated = []
        for form in answer_forms(candidate):
            candidate_generated.extend(keystr_forms(form, newline_variants=True))
        generated.extend(candidate_generated)
        candidate_passphrases[candidate] = set(candidate_generated)

    shared_passphrases, overlap_groups = oracle_overlap(candidate_passphrases, ordered)
    manifest = wordlist_manifest()
    candidate_rows = []
    for index, candidate in enumerate(ordered, 1):
        sources_for_candidate = tuple(provenance[candidate])
        source_tiers = tuple(dict.fromkeys(SOURCE_META[source][0] for source in sources_for_candidate))
        candidate_rows.append({
            "index": index,
            "candidate": candidate,
            "sources": sources_for_candidate,
            "source_tiers": source_tiers,
            "first_source_tier": source_tiers[0],
        })

    return {
        "include_seed_exact_leads": include_seed,
        "candidate_count": len(ordered),
        "digest": candidate_list_digest(ordered),
        "active_source_lines": sum(row["active_lines"] for row in source_rows),
        "source_count": len(source_rows),
        "source_rows": source_rows,
        "multi_source_candidate_count": sum(len(rows) > 1 for rows in provenance.values()),
        "cross_source_tier_candidate_count": sum(
            len(row["source_tiers"]) > 1 for row in candidate_rows
        ),
        "first_source_tier_counts": dict(Counter(row["first_source_tier"] for row in candidate_rows)),
        "wordlist_manifest": manifest,
        "included_wordlist_count": sum(row["status"] == "included" for row in manifest),
        "excluded_wordlist_count": sum(row["status"] == "excluded" for row in manifest),
        "oracle_overlap_groups": len(overlap_groups),
        "oracle_overlap_candidates": sum(map(len, overlap_groups)),
        "shared_generated_passphrases": shared_passphrases,
        "candidate_form_evaluations": len(generated),
        "unique_generated_passphrases": len(set(generated)),
        "duplicate_generated_evaluations": len(generated) - len(set(generated)),
        "candidates": tuple(candidate_rows),
        "oracle_overlap_candidate_groups": overlap_groups,
    }


def self_test():
    base = build(False)
    seed = build(True)
    assert tuple(row["candidate"] for row in base["candidates"]) == tuple(load_curated_candidates())
    assert (base["candidate_count"], base["digest"]) == (EXPECTED_BASE_COUNT, EXPECTED_BASE_DIGEST)
    assert (seed["candidate_count"], seed["digest"]) == (EXPECTED_SEED_COUNT, EXPECTED_SEED_DIGEST)
    assert sum(row["new_exact"] for row in base["source_rows"]) == EXPECTED_BASE_COUNT
    actual_source_accounting = {
        row["source"]: (
            row["active_lines"], row["unique_in_source"],
            row["new_exact"], row["duplicate_of_prior"],
        )
        for row in base["source_rows"]
    }
    assert actual_source_accounting == EXPECTED_SOURCE_ACCOUNTING
    for key, expected in EXPECTED_BASE_HEADLINES.items():
        assert base[key] == expected, (key, base[key], expected)
    assert base["first_source_tier_counts"] == {
        "direct": 98, "bounded": 243, "thematic": 225, "mixed": 82,
    }
    # 28, not 26: macro_clue_permutation_combinations.txt (Phase 322) and
    # macro_clue_permutation_combinations_k8.txt (Phase 334) added 2026-08-20
    # by a concurrent session, classified "dedicated-audit" (both already
    # swept separately via tools/gpu_oracle, both rejected) -- doesn't touch
    # the 648-candidate corpus itself, digest/count unchanged.
    assert (base["included_wordlist_count"], base["excluded_wordlist_count"]) == (23, 28)
    assert seed["candidate_form_evaluations"] == 17073
    assert seed["unique_generated_passphrases"] == 14587
    assert seed["duplicate_generated_evaluations"] == 2486
    assert seed["candidates"][-2]["candidate"] == "SEED"
    assert seed["candidates"][-1]["candidate"] == "IZLKESEEDQPPEN"
    print("[*] self-test OK: base 648/digest and SEED 650/digest, provenance, and source accounting")


def print_summary(report):
    print(f"candidates: {report['candidate_count']}")
    print(f"digest: {report['digest']}")
    print(f"active source lines: {report['active_source_lines']}")
    print(f"generated evaluations: {report['candidate_form_evaluations']}")
    print(f"unique generated passphrases: {report['unique_generated_passphrases']}")
    print(f"oracle-overlap groups/candidates: {report['oracle_overlap_groups']}/{report['oracle_overlap_candidates']}")
    print(f"included/excluded wordlists: {report['included_wordlist_count']}/{report['excluded_wordlist_count']}")
    print("\nsource\ttier\tactive\tunique\tnew\tprior-duplicates\trationale")
    for row in report["source_rows"]:
        print("\t".join(map(str, (
            row["source"], row["tier"], row["active_lines"],
            row["unique_in_source"], row["new_exact"], row["duplicate_of_prior"],
            row["rationale"],
        ))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-seed", action="store_true", help="include the two Phase-253 exact SEED leads")
    parser.add_argument("--candidate", help="show exact provenance for one candidate (case-sensitive)")
    parser.add_argument("--list", action="store_true", help="print the full ordered candidate/provenance list")
    parser.add_argument("--json", action="store_true", help="emit the complete machine-readable report")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = build(args.include_seed)
    if args.json:
        print(json.dumps(report, indent=2))
    elif args.candidate:
        matches = [row for row in report["candidates"] if row["candidate"] == args.candidate]
        print(json.dumps(matches, indent=2))
    elif args.list:
        for row in report["candidates"]:
            print(f"{row['index']:03d}\t{row['candidate']}\t{','.join(row['sources'])}\t{','.join(row['source_tiers'])}\t{row['first_source_tier']}")
    else:
        print_summary(report)


if __name__ == "__main__":
    main()
